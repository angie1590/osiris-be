from __future__ import annotations

from fastapi import HTTPException
from sqlmodel import Session, select

from osiris.modules.facturacion.entity import Venta, VentaDetalle, VentaDetalleImpuesto
from osiris.modules.facturacion.models import (
    ImpuestoAplicadoInput,
    VentaCompraDetalleCreate,
    VentaCreate,
    VentaDetalleImpuestoRead,
    VentaDetalleRead,
    VentaRead,
    VentaRegistroCreate,
    q2,
)
from osiris.modules.inventario.movimiento_inventario.entity import (
    InventarioStock,
    TipoMovimientoInventario,
)
from osiris.modules.inventario.movimiento_inventario.models import MovimientoInventarioCreate
from osiris.modules.inventario.movimiento_inventario.service import MovimientoInventarioService
from osiris.modules.inventario.producto.entity import Producto, ProductoImpuesto


class VentaService:
    def __init__(self) -> None:
        self.movimiento_service = MovimientoInventarioService()

    @staticmethod
    def _es_session_real(session: Session) -> bool:
        return isinstance(session, Session)

    @staticmethod
    def _snapshot_impuestos_producto(session: Session, producto_id) -> list[ImpuestoAplicadoInput]:
        stmt = select(ProductoImpuesto).where(
            ProductoImpuesto.producto_id == producto_id,
            ProductoImpuesto.activo.is_(True),
        )
        impuestos = list(session.exec(stmt).all())
        if not impuestos:
            raise HTTPException(
                status_code=400,
                detail=f"El producto {producto_id} no tiene impuestos configurados.",
            )

        snapshots: list[ImpuestoAplicadoInput] = []
        for impuesto in impuestos:
            if impuesto.codigo_impuesto_sri == "2":
                tipo = "IVA"
            elif impuesto.codigo_impuesto_sri == "3":
                tipo = "ICE"
            else:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Impuesto {impuesto.id} del producto {producto_id} no es compatible "
                        "con catalogo MVP (solo IVA/ICE)."
                    ),
                )

            snapshots.append(
                ImpuestoAplicadoInput(
                    tipo_impuesto=tipo,
                    codigo_impuesto_sri=impuesto.codigo_impuesto_sri,
                    codigo_porcentaje_sri=impuesto.codigo_porcentaje_sri,
                    tarifa=impuesto.tarifa,
                )
            )
        return snapshots

    def hidratar_venta_desde_productos(self, session: Session, payload: VentaRegistroCreate) -> VentaCreate:
        detalles: list[VentaCompraDetalleCreate] = []
        for detalle in payload.detalles:
            producto = session.get(Producto, detalle.producto_id)
            if not producto or not producto.activo:
                raise HTTPException(
                    status_code=404,
                    detail=f"Producto {detalle.producto_id} no encontrado o inactivo.",
                )

            impuestos = self._snapshot_impuestos_producto(session, detalle.producto_id)
            detalles.append(
                VentaCompraDetalleCreate(
                    producto_id=detalle.producto_id,
                    descripcion=detalle.descripcion,
                    cantidad=detalle.cantidad,
                    precio_unitario=detalle.precio_unitario,
                    descuento=detalle.descuento,
                    es_actividad_excluida=detalle.es_actividad_excluida,
                    impuestos=impuestos,
                )
            )

        return VentaCreate(
            fecha_emision=payload.fecha_emision,
            bodega_id=payload.bodega_id,
            tipo_identificacion_comprador=payload.tipo_identificacion_comprador,
            identificacion_comprador=payload.identificacion_comprador,
            forma_pago=payload.forma_pago,
            regimen_emisor=payload.regimen_emisor,
            usuario_auditoria=payload.usuario_auditoria,
            detalles=detalles,
        )

    def _resolver_bodega_para_venta(self, session: Session, payload: VentaCreate):
        if payload.bodega_id is not None:
            return payload.bodega_id
        if not payload.detalles:
            raise HTTPException(status_code=400, detail="La venta no tiene detalles para orquestar inventario.")

        producto_referencia = payload.detalles[0].producto_id
        stocks_referencia = list(
            session.exec(
                select(InventarioStock).where(
                    InventarioStock.producto_id == producto_referencia,
                    InventarioStock.activo.is_(True),
                )
            ).all()
        )
        if not stocks_referencia:
            raise HTTPException(
                status_code=400,
                detail=f"No existe stock materializado para el producto {producto_referencia}.",
            )
        bodega_id = stocks_referencia[0].bodega_id

        for detalle in payload.detalles:
            stock_detalle = session.exec(
                select(InventarioStock).where(
                    InventarioStock.bodega_id == bodega_id,
                    InventarioStock.producto_id == detalle.producto_id,
                    InventarioStock.activo.is_(True),
                )
            ).first()
            if stock_detalle is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"El producto {detalle.producto_id} no tiene stock materializado "
                        f"en la bodega {bodega_id}."
                    ),
                )
        return bodega_id

    def _orquestar_egreso_inventario(self, session: Session, venta: Venta, payload: VentaCreate) -> None:
        if not self._es_session_real(session):
            return

        bodega_id = self._resolver_bodega_para_venta(session, payload)
        movimiento_payload = MovimientoInventarioCreate(
            bodega_id=bodega_id,
            tipo_movimiento=TipoMovimientoInventario.EGRESO,
            referencia_documento=f"VENTA:{venta.id}",
            usuario_auditoria=payload.usuario_auditoria,
            detalles=[
                {
                    "producto_id": detalle.producto_id,
                    "cantidad": detalle.cantidad,
                    "costo_unitario": detalle.precio_unitario,
                }
                for detalle in payload.detalles
            ],
        )
        movimiento = self.movimiento_service.crear_movimiento_borrador(
            session,
            movimiento_payload,
            commit=False,
        )
        try:
            self.movimiento_service.confirmar_movimiento(
                session,
                movimiento.id,
                commit=False,
                rollback_on_error=False,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    def registrar_venta(self, session: Session, payload: VentaCreate) -> Venta:
        try:
            venta = Venta(
                fecha_emision=payload.fecha_emision,
                tipo_identificacion_comprador=payload.tipo_identificacion_comprador,
                identificacion_comprador=payload.identificacion_comprador,
                forma_pago=payload.forma_pago,
                regimen_emisor=payload.regimen_emisor,
                subtotal_sin_impuestos=payload.subtotal_sin_impuestos,
                subtotal_12=payload.subtotal_12,
                subtotal_15=payload.subtotal_15,
                subtotal_0=payload.subtotal_0,
                subtotal_no_objeto=payload.subtotal_no_objeto,
                monto_iva=payload.monto_iva,
                monto_ice=payload.monto_ice,
                valor_total=payload.valor_total,
                usuario_auditoria=payload.usuario_auditoria,
            )
            session.add(venta)
            session.flush()

            for detalle in payload.detalles:
                detalle_db = VentaDetalle(
                    venta_id=venta.id,
                    producto_id=detalle.producto_id,
                    descripcion=detalle.descripcion,
                    cantidad=detalle.cantidad,
                    precio_unitario=detalle.precio_unitario,
                    descuento=detalle.descuento,
                    subtotal_sin_impuesto=q2(detalle.subtotal_sin_impuesto),
                    es_actividad_excluida=detalle.es_actividad_excluida,
                    usuario_auditoria=payload.usuario_auditoria,
                )
                session.add(detalle_db)
                session.flush()

                for impuesto in detalle.impuestos:
                    snapshot = VentaDetalleImpuesto(
                        venta_detalle_id=detalle_db.id,
                        tipo_impuesto=impuesto.tipo_impuesto,
                        codigo_impuesto_sri=impuesto.codigo_impuesto_sri,
                        codigo_porcentaje_sri=impuesto.codigo_porcentaje_sri,
                        tarifa=impuesto.tarifa,
                        base_imponible=detalle.base_imponible_impuesto(impuesto),
                        valor_impuesto=detalle.valor_impuesto(impuesto),
                        usuario_auditoria=payload.usuario_auditoria,
                    )
                    session.add(snapshot)

            self._orquestar_egreso_inventario(session, venta, payload)

            session.commit()
            session.refresh(venta)
            return venta
        except Exception:
            if self._es_session_real(session):
                session.rollback()
            raise

    def registrar_venta_desde_productos(self, session: Session, payload: VentaRegistroCreate) -> Venta:
        venta_create = self.hidratar_venta_desde_productos(session, payload)
        return self.registrar_venta(session, venta_create)

    def obtener_venta_read(self, session: Session, venta_id) -> VentaRead:
        venta = session.get(Venta, venta_id)
        if not venta or not venta.activo:
            raise HTTPException(status_code=404, detail="Venta no encontrada")

        stmt_detalle = select(VentaDetalle).where(
            VentaDetalle.venta_id == venta.id,
            VentaDetalle.activo.is_(True),
        )
        detalles_db = list(session.exec(stmt_detalle).all())

        detalles_read: list[VentaDetalleRead] = []
        for detalle in detalles_db:
            stmt_impuestos = select(VentaDetalleImpuesto).where(
                VentaDetalleImpuesto.venta_detalle_id == detalle.id,
                VentaDetalleImpuesto.activo.is_(True),
            )
            impuestos_db = list(session.exec(stmt_impuestos).all())
            impuestos_read = [
                VentaDetalleImpuestoRead(
                    tipo_impuesto=imp.tipo_impuesto,
                    codigo_impuesto_sri=imp.codigo_impuesto_sri,
                    codigo_porcentaje_sri=imp.codigo_porcentaje_sri,
                    tarifa=imp.tarifa,
                    base_imponible=imp.base_imponible,
                    valor_impuesto=imp.valor_impuesto,
                )
                for imp in impuestos_db
            ]

            detalles_read.append(
                VentaDetalleRead(
                    producto_id=detalle.producto_id,
                    descripcion=detalle.descripcion,
                    cantidad=detalle.cantidad,
                    precio_unitario=detalle.precio_unitario,
                    descuento=detalle.descuento,
                    subtotal_sin_impuesto=detalle.subtotal_sin_impuesto,
                    es_actividad_excluida=detalle.es_actividad_excluida,
                    impuestos=impuestos_read,
                )
            )

        return VentaRead(
            id=venta.id,
            fecha_emision=venta.fecha_emision,
            tipo_identificacion_comprador=venta.tipo_identificacion_comprador,
            identificacion_comprador=venta.identificacion_comprador,
            forma_pago=venta.forma_pago,
            regimen_emisor=venta.regimen_emisor,
            subtotal_sin_impuestos=venta.subtotal_sin_impuestos,
            subtotal_12=venta.subtotal_12,
            subtotal_15=venta.subtotal_15,
            subtotal_0=venta.subtotal_0,
            subtotal_no_objeto=venta.subtotal_no_objeto,
            monto_iva=venta.monto_iva,
            monto_ice=venta.monto_ice,
            valor_total=venta.valor_total,
            detalles=detalles_read,
            creado_en=venta.creado_en,
            actualizado_en=venta.actualizado_en,
        )
