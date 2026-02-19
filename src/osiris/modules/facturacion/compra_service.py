from __future__ import annotations

from fastapi import HTTPException
from sqlmodel import Session, select

from osiris.modules.facturacion.entity import Compra, CompraDetalle, CompraDetalleImpuesto
from osiris.modules.facturacion.models import (
    CompraCreate,
    CompraRegistroCreate,
    ImpuestoAplicadoInput,
    VentaCompraDetalleCreate,
    q2,
)
from osiris.modules.inventario.bodega.entity import Bodega
from osiris.modules.inventario.movimiento_inventario.entity import TipoMovimientoInventario
from osiris.modules.inventario.movimiento_inventario.models import MovimientoInventarioCreate
from osiris.modules.inventario.movimiento_inventario.service import MovimientoInventarioService
from osiris.modules.inventario.producto.entity import Producto, ProductoImpuesto


class CompraService:
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

    def hidratar_compra_desde_productos(self, session: Session, payload: CompraRegistroCreate) -> CompraCreate:
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

        return CompraCreate(
            fecha_emision=payload.fecha_emision,
            bodega_id=payload.bodega_id,
            tipo_identificacion_proveedor=payload.tipo_identificacion_proveedor,
            identificacion_proveedor=payload.identificacion_proveedor,
            forma_pago=payload.forma_pago,
            usuario_auditoria=payload.usuario_auditoria,
            detalles=detalles,
        )

    def _resolver_bodega_para_compra(self, session: Session, payload: CompraCreate):
        if payload.bodega_id is not None:
            return payload.bodega_id

        bodegas = list(
            session.exec(select(Bodega.id).where(Bodega.activo.is_(True))).all()
        )
        if len(bodegas) == 1:
            return bodegas[0]
        raise HTTPException(
            status_code=400,
            detail="Debe enviar bodega_id para registrar la compra.",
        )

    def _orquestar_ingreso_inventario(self, session: Session, compra: Compra, payload: CompraCreate) -> None:
        if not self._es_session_real(session):
            return

        bodega_id = self._resolver_bodega_para_compra(session, payload)
        movimiento_payload = MovimientoInventarioCreate(
            bodega_id=bodega_id,
            tipo_movimiento=TipoMovimientoInventario.INGRESO,
            referencia_documento=f"COMPRA:{compra.id}",
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
        self.movimiento_service.confirmar_movimiento(
            session,
            movimiento.id,
            commit=False,
            rollback_on_error=False,
        )

    def registrar_compra(self, session: Session, payload: CompraCreate) -> Compra:
        try:
            compra = Compra(
                fecha_emision=payload.fecha_emision,
                tipo_identificacion_proveedor=payload.tipo_identificacion_proveedor,
                identificacion_proveedor=payload.identificacion_proveedor,
                forma_pago=payload.forma_pago,
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
            session.add(compra)
            session.flush()

            for detalle in payload.detalles:
                detalle_db = CompraDetalle(
                    compra_id=compra.id,
                    producto_id=detalle.producto_id,
                    descripcion=detalle.descripcion,
                    cantidad=detalle.cantidad,
                    precio_unitario=detalle.precio_unitario,
                    descuento=detalle.descuento,
                    subtotal_sin_impuesto=q2(detalle.subtotal_sin_impuesto),
                    usuario_auditoria=payload.usuario_auditoria,
                )
                session.add(detalle_db)
                session.flush()

                for impuesto in detalle.impuestos:
                    snapshot = CompraDetalleImpuesto(
                        compra_detalle_id=detalle_db.id,
                        tipo_impuesto=impuesto.tipo_impuesto,
                        codigo_impuesto_sri=impuesto.codigo_impuesto_sri,
                        codigo_porcentaje_sri=impuesto.codigo_porcentaje_sri,
                        tarifa=impuesto.tarifa,
                        base_imponible=detalle.base_imponible_impuesto(impuesto),
                        valor_impuesto=detalle.valor_impuesto(impuesto),
                        usuario_auditoria=payload.usuario_auditoria,
                    )
                    session.add(snapshot)

            self._orquestar_ingreso_inventario(session, compra, payload)

            session.commit()
            session.refresh(compra)
            return compra
        except Exception:
            if self._es_session_real(session):
                session.rollback()
            raise

    def registrar_compra_desde_productos(self, session: Session, payload: CompraRegistroCreate) -> Compra:
        compra_create = self.hidratar_compra_desde_productos(session, payload)
        return self.registrar_compra(session, compra_create)
