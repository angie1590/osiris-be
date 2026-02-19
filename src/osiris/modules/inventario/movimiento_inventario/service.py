from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.orm.exc import NoResultFound
from sqlmodel import Session, select

from osiris.modules.inventario.movimiento_inventario.entity import (
    EstadoMovimientoInventario,
    InventarioStock,
    MovimientoInventario,
    MovimientoInventarioDetalle,
    TipoMovimientoInventario,
)
from osiris.modules.inventario.movimiento_inventario.models import MovimientoInventarioCreate


Q4 = Decimal("0.0001")


def q4(value: Decimal | int | str) -> Decimal:
    return Decimal(str(value)).quantize(Q4, rounding=ROUND_HALF_UP)


class MovimientoInventarioService:
    def crear_movimiento_borrador(
        self,
        session: Session,
        payload: MovimientoInventarioCreate,
    ) -> MovimientoInventario:
        movimiento = MovimientoInventario(
            fecha=payload.fecha,
            bodega_id=payload.bodega_id,
            tipo_movimiento=payload.tipo_movimiento,
            estado=EstadoMovimientoInventario.BORRADOR,
            referencia_documento=payload.referencia_documento,
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
        session.commit()
        session.refresh(movimiento)
        return movimiento

    def confirmar_movimiento(
        self,
        session: Session,
        movimiento_id,
    ) -> MovimientoInventario:
        movimiento = session.get(MovimientoInventario, movimiento_id)
        if not movimiento or not movimiento.activo:
            raise HTTPException(status_code=404, detail="Movimiento de inventario no encontrado")
        if movimiento.estado != EstadoMovimientoInventario.BORRADOR:
            raise HTTPException(status_code=400, detail="Solo se puede confirmar movimientos en BORRADOR")

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

        try:
            for detalle in detalles:
                if movimiento.tipo_movimiento in {TipoMovimientoInventario.EGRESO, TipoMovimientoInventario.TRANSFERENCIA}:
                    self._aplicar_egreso_con_lock(session, movimiento, detalle)
                else:
                    self._aplicar_ingreso(session, movimiento, detalle)

            movimiento.estado = EstadoMovimientoInventario.CONFIRMADO
            session.add(movimiento)
            session.commit()
            session.refresh(movimiento)
            return movimiento
        except Exception:
            session.rollback()
            raise

    def _aplicar_egreso_con_lock(
        self,
        session: Session,
        movimiento: MovimientoInventario,
        detalle: MovimientoInventarioDetalle,
    ) -> None:
        try:
            stock = (
                session.query(InventarioStock)
                .with_for_update()
                .filter_by(
                    bodega_id=movimiento.bodega_id,
                    producto_id=detalle.producto_id,
                    activo=True,
                )
                .one()
            )
        except NoResultFound as exc:
            raise ValueError("No existe stock materializado para el producto/bodega.") from exc

        cantidad_actual = q4(stock.cantidad_actual)
        cantidad_detalle = q4(detalle.cantidad)
        if cantidad_actual - cantidad_detalle < Decimal("0"):
            raise ValueError("Inventario insuficiente: no se permite stock negativo.")

        # E3-3: congelar costo histórico del egreso al costo promedio vigente.
        detalle.costo_unitario = q4(stock.costo_promedio_vigente)
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
        stock = (
            session.query(InventarioStock)
            .with_for_update()
            .filter_by(
                bodega_id=movimiento.bodega_id,
                producto_id=detalle.producto_id,
                activo=True,
            )
            .one_or_none()
        )
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

        nuevo_costo = q4(
            ((cantidad_actual * costo_actual) + (cantidad_ingreso * costo_ingreso)) / nueva_cantidad
        )

        stock.cantidad_actual = nueva_cantidad
        stock.costo_promedio_vigente = nuevo_costo
        session.add(stock)
