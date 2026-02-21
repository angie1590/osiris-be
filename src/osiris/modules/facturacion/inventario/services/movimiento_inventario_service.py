from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.orm.exc import NoResultFound
from sqlmodel import Session, select

from osiris.modules.facturacion.core_sri.services.template_method import TemplateMethodService
from osiris.modules.facturacion.inventario.strategies.calculo_kardex_strategy import CalculoKardexStrategy
from osiris.modules.facturacion.inventario.models import (
    EstadoMovimientoInventario,
    InventarioStock,
    MovimientoInventario,
    MovimientoInventarioDetalle,
    TipoMovimientoInventario,
)
from osiris.modules.facturacion.inventario.schemas import (
    MovimientoInventarioCreate,
    MovimientoInventarioDetalleRead,
    MovimientoInventarioRead,
)
from osiris.modules.common.audit_log.entity import AuditLog


Q4 = Decimal("0.0001")


def q4(value: Decimal | int | str) -> Decimal:
    return Decimal(str(value)).quantize(Q4, rounding=ROUND_HALF_UP)


class MovimientoInventarioService(TemplateMethodService[MovimientoInventarioCreate, MovimientoInventario]):
    def __init__(self, calculo_kardex_strategy: CalculoKardexStrategy | None = None) -> None:
        self.calculo_kardex_strategy = calculo_kardex_strategy or CalculoKardexStrategy()

    def crear_movimiento_borrador(
        self,
        session: Session,
        payload: MovimientoInventarioCreate,
        *,
        commit: bool = True,
    ) -> MovimientoInventario:
        return self.execute_create(session, payload, commit=commit)

    def _execute_create(
        self,
        session: Session,
        payload: MovimientoInventarioCreate,
        *,
        context: dict,
        **kwargs,
    ) -> MovimientoInventario:
        commit = kwargs.get("commit", True)
        _ = context
        movimiento = MovimientoInventario(
            fecha=payload.fecha,
            bodega_id=payload.bodega_id,
            tipo_movimiento=payload.tipo_movimiento,
            estado=EstadoMovimientoInventario.BORRADOR,
            referencia_documento=payload.referencia_documento,
            motivo_ajuste=payload.motivo_ajuste,
            usuario_auditoria=payload.usuario_auditoria,
            activo=True,
        )
        session.add(movimiento)
        session.flush()

        for detalle in payload.detalles:
            movimiento_detalle = MovimientoInventarioDetalle(
                movimiento_inventario_id=movimiento.id,
                producto_id=detalle.producto_id,
                cantidad=detalle.cantidad,
                costo_unitario=detalle.costo_unitario,
                usuario_auditoria=payload.usuario_auditoria,
                activo=True,
            )
            session.add(movimiento_detalle)

        # Regla de la card E3-1: BORRADOR no altera stock.
        if commit:
            session.commit()
            session.refresh(movimiento)
        else:
            session.flush()
        return movimiento

    def confirmar_movimiento(
        self,
        session: Session,
        movimiento_id,
        *,
        motivo_ajuste: str | None = None,
        usuario_autorizador: str | None = None,
        commit: bool = True,
        rollback_on_error: bool = True,
    ) -> MovimientoInventario:
        movimiento = session.get(MovimientoInventario, movimiento_id)
        if not movimiento or not movimiento.activo:
            raise HTTPException(status_code=404, detail="Movimiento de inventario no encontrado")
        if movimiento.estado != EstadoMovimientoInventario.BORRADOR:
            raise HTTPException(status_code=400, detail="Solo se puede confirmar movimientos en BORRADOR")

        if usuario_autorizador:
            movimiento.usuario_auditoria = usuario_autorizador
        if motivo_ajuste is not None:
            motivo_limpio = motivo_ajuste.strip()
            movimiento.motivo_ajuste = motivo_limpio or None
        if (
            movimiento.tipo_movimiento == TipoMovimientoInventario.AJUSTE
            and (not movimiento.motivo_ajuste or not movimiento.motivo_ajuste.strip())
        ):
            raise HTTPException(
                status_code=400,
                detail="motivo_ajuste es obligatorio para confirmar movimientos de tipo AJUSTE.",
            )

        detalles = list(
            session.exec(
                select(MovimientoInventarioDetalle).where(
                    MovimientoInventarioDetalle.movimiento_inventario_id == movimiento.id,
                    MovimientoInventarioDetalle.activo.is_(True),
                )
            ).all()
        )
        if not detalles:
            raise ValueError("No se puede confirmar un movimiento sin detalles")

        estado_anterior = movimiento.estado.value
        try:
            for detalle in detalles:
                if movimiento.tipo_movimiento in {TipoMovimientoInventario.EGRESO, TipoMovimientoInventario.TRANSFERENCIA}:
                    self._aplicar_egreso_con_lock(session, movimiento, detalle)
                else:
                    self._aplicar_ingreso(session, movimiento, detalle)

            movimiento.estado = EstadoMovimientoInventario.CONFIRMADO
            session.add(movimiento)
            if movimiento.tipo_movimiento == TipoMovimientoInventario.AJUSTE:
                self._registrar_auditoria_ajuste(
                    session,
                    movimiento=movimiento,
                    estado_anterior=estado_anterior,
                )
            if commit:
                session.commit()
                session.refresh(movimiento)
            else:
                session.flush()
            return movimiento
        except Exception:
            if rollback_on_error:
                session.rollback()
            raise

    def _registrar_auditoria_ajuste(
        self,
        session: Session,
        *,
        movimiento: MovimientoInventario,
        estado_anterior: str,
    ) -> None:
        usuario_autorizador = movimiento.usuario_auditoria or movimiento.updated_by or movimiento.created_by
        estado_nuevo = {
            "estado": movimiento.estado.value,
            "tipo_movimiento": movimiento.tipo_movimiento.value,
            "bodega_id": str(movimiento.bodega_id),
            "motivo_ajuste": movimiento.motivo_ajuste,
            "usuario_autorizador": usuario_autorizador,
        }
        session.add(
            AuditLog(
                tabla_afectada="tbl_movimiento_inventario",
                registro_id=str(movimiento.id),
                entidad="MovimientoInventario",
                entidad_id=movimiento.id,
                accion="AJUSTE",
                estado_anterior={"estado": estado_anterior},
                estado_nuevo=estado_nuevo,
                before_json={"estado": estado_anterior},
                after_json=estado_nuevo,
                usuario_id=usuario_autorizador,
                usuario_auditoria=usuario_autorizador,
                fecha=datetime.utcnow(),
            )
        )

    def _aplicar_egreso_con_lock(
        self,
        session: Session,
        movimiento: MovimientoInventario,
        detalle: MovimientoInventarioDetalle,
    ) -> None:
        try:
            stock = session.exec(
                select(InventarioStock)
                .where(
                    InventarioStock.bodega_id == movimiento.bodega_id,
                    InventarioStock.producto_id == detalle.producto_id,
                    InventarioStock.activo.is_(True),
                )
                .with_for_update()
            ).one()
        except NoResultFound as exc:
            raise ValueError("No existe stock materializado para el producto/bodega.") from exc

        cantidad_actual = q4(stock.cantidad_actual)
        cantidad_detalle = q4(detalle.cantidad)
        if cantidad_actual - cantidad_detalle < Decimal("0"):
            raise ValueError("Inventario insuficiente: no se permite stock negativo.")

        # E3-3: congelar costo histórico del egreso al costo promedio vigente.
        detalle.costo_unitario = self.calculo_kardex_strategy.congelar_costo_egreso(stock.costo_promedio_vigente)
        session.add(detalle)

        result = session.exec(
            update(InventarioStock)
            .where(
                InventarioStock.id == stock.id,
                InventarioStock.activo.is_(True),
                InventarioStock.cantidad_actual >= cantidad_detalle,
            )
            .values(cantidad_actual=InventarioStock.cantidad_actual - cantidad_detalle)
        )
        if (getattr(result, "rowcount", 0) or 0) != 1:
            raise ValueError("Inventario insuficiente: no se permite stock negativo.")

    def _aplicar_ingreso(
        self,
        session: Session,
        movimiento: MovimientoInventario,
        detalle: MovimientoInventarioDetalle,
    ) -> None:
        stock = session.exec(
            select(InventarioStock)
            .where(
                InventarioStock.bodega_id == movimiento.bodega_id,
                InventarioStock.producto_id == detalle.producto_id,
                InventarioStock.activo.is_(True),
            )
            .with_for_update()
        ).one_or_none()
        if stock is None:
            stock = InventarioStock(
                bodega_id=movimiento.bodega_id,
                producto_id=detalle.producto_id,
                cantidad_actual=Decimal("0.0000"),
                costo_promedio_vigente=Decimal("0.0000"),
                usuario_auditoria=movimiento.usuario_auditoria,
                activo=True,
            )
            session.add(stock)
            session.flush()

        cantidad_actual = q4(stock.cantidad_actual)
        costo_actual = q4(stock.costo_promedio_vigente)
        cantidad_ingreso = q4(detalle.cantidad)
        costo_ingreso = q4(detalle.costo_unitario)

        nueva_cantidad = q4(cantidad_actual + cantidad_ingreso)
        if nueva_cantidad <= Decimal("0"):
            raise ValueError("Cantidad resultante invalida para ingreso.")

        nuevo_costo = self.calculo_kardex_strategy.calcular_nuevo_costo_promedio(
            cantidad_actual=cantidad_actual,
            costo_promedio_actual=costo_actual,
            cantidad_ingresada=cantidad_ingreso,
            costo_nuevo=costo_ingreso,
        )

        stock.cantidad_actual = nueva_cantidad
        stock.costo_promedio_vigente = nuevo_costo
        session.add(stock)

    def obtener_kardex(
        self,
        session: Session,
        *,
        producto_id: UUID,
        bodega_id: UUID,
        fecha_inicio=None,
        fecha_fin=None,
    ) -> dict:
        filtros_base = [
            MovimientoInventario.bodega_id == bodega_id,
            MovimientoInventario.estado == EstadoMovimientoInventario.CONFIRMADO,
            MovimientoInventarioDetalle.producto_id == producto_id,
            MovimientoInventario.activo.is_(True),
            MovimientoInventarioDetalle.activo.is_(True),
        ]

        saldo_inicial = Decimal("0.0000")
        if fecha_inicio is not None:
            filas_saldo = session.exec(
                select(
                    MovimientoInventario.tipo_movimiento,
                    MovimientoInventarioDetalle.cantidad,
                )
                .join(
                    MovimientoInventarioDetalle,
                    MovimientoInventarioDetalle.movimiento_inventario_id == MovimientoInventario.id,
                )
                .where(
                    *filtros_base,
                    MovimientoInventario.fecha < fecha_inicio,
                )
            ).all()
            for tipo_movimiento, cantidad in filas_saldo:
                cantidad_q = q4(cantidad)
                if tipo_movimiento in {TipoMovimientoInventario.EGRESO, TipoMovimientoInventario.TRANSFERENCIA}:
                    saldo_inicial = q4(saldo_inicial - cantidad_q)
                else:
                    saldo_inicial = q4(saldo_inicial + cantidad_q)

        filtros_movimientos = list(filtros_base)
        if fecha_inicio is not None:
            filtros_movimientos.append(MovimientoInventario.fecha >= fecha_inicio)
        if fecha_fin is not None:
            filtros_movimientos.append(MovimientoInventario.fecha <= fecha_fin)

        filas = session.exec(
            select(MovimientoInventario, MovimientoInventarioDetalle)
            .join(
                MovimientoInventarioDetalle,
                MovimientoInventarioDetalle.movimiento_inventario_id == MovimientoInventario.id,
            )
            .where(*filtros_movimientos)
            .order_by(
                MovimientoInventario.fecha.asc(),
                MovimientoInventario.creado_en.asc(),
                MovimientoInventarioDetalle.id.asc(),
            )
        ).all()

        saldo = q4(saldo_inicial)
        movimientos = []
        for movimiento, detalle in filas:
            cantidad = q4(detalle.cantidad)
            costo = q4(detalle.costo_unitario)
            if movimiento.tipo_movimiento in {TipoMovimientoInventario.EGRESO, TipoMovimientoInventario.TRANSFERENCIA}:
                entrada = Decimal("0.0000")
                salida = cantidad
                saldo = q4(saldo - cantidad)
                valor = q4(salida * costo)
            else:
                entrada = cantidad
                salida = Decimal("0.0000")
                saldo = q4(saldo + cantidad)
                valor = q4(entrada * costo)

            movimientos.append(
                {
                    "fecha": movimiento.fecha,
                    "movimiento_id": movimiento.id,
                    "tipo_movimiento": movimiento.tipo_movimiento,
                    "referencia_documento": movimiento.referencia_documento,
                    "cantidad_entrada": entrada,
                    "cantidad_salida": salida,
                    "saldo_cantidad": saldo,
                    "costo_unitario_aplicado": costo,
                    "valor_movimiento": valor,
                }
            )

        return {
            "producto_id": producto_id,
            "bodega_id": bodega_id,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "saldo_inicial": saldo_inicial,
            "movimientos": movimientos,
        }

    def obtener_valoracion(
        self,
        session: Session,
    ) -> dict:
        stocks = session.exec(
            select(InventarioStock).where(InventarioStock.activo.is_(True))
        ).all()

        agrupado: dict[UUID, dict] = {}
        total_global = Decimal("0.0000")
        for stock in stocks:
            cantidad = q4(stock.cantidad_actual)
            costo = q4(stock.costo_promedio_vigente)
            valor_total = q4(cantidad * costo)
            total_global = q4(total_global + valor_total)

            if stock.bodega_id not in agrupado:
                agrupado[stock.bodega_id] = {
                    "bodega_id": stock.bodega_id,
                    "total_bodega": Decimal("0.0000"),
                    "productos": [],
                }

            agrupado[stock.bodega_id]["productos"].append(
                {
                    "producto_id": stock.producto_id,
                    "cantidad_actual": cantidad,
                    "costo_promedio_vigente": costo,
                    "valor_total": valor_total,
                }
            )
            agrupado[stock.bodega_id]["total_bodega"] = q4(
                agrupado[stock.bodega_id]["total_bodega"] + valor_total
            )

        return {
            "bodegas": list(agrupado.values()),
            "total_global": total_global,
        }

    def obtener_movimiento_read(self, session: Session, movimiento_id) -> MovimientoInventarioRead:
        movimiento = session.get(MovimientoInventario, movimiento_id)
        if not movimiento or not movimiento.activo:
            raise HTTPException(status_code=404, detail="Movimiento de inventario no encontrado")

        detalles = list(
            session.exec(
                select(MovimientoInventarioDetalle).where(
                    MovimientoInventarioDetalle.movimiento_inventario_id == movimiento.id,
                    MovimientoInventarioDetalle.activo.is_(True),
                )
            ).all()
        )
        detalles_read = [
            MovimientoInventarioDetalleRead(
                id=detalle.id,
                movimiento_inventario_id=detalle.movimiento_inventario_id,
                producto_id=detalle.producto_id,
                cantidad=detalle.cantidad,
                costo_unitario=detalle.costo_unitario,
            )
            for detalle in detalles
        ]

        return MovimientoInventarioRead(
            id=movimiento.id,
            fecha=movimiento.fecha,
            bodega_id=movimiento.bodega_id,
            tipo_movimiento=movimiento.tipo_movimiento,
            estado=movimiento.estado,
            referencia_documento=movimiento.referencia_documento,
            motivo_ajuste=movimiento.motivo_ajuste,
            detalles=detalles_read,
        )
