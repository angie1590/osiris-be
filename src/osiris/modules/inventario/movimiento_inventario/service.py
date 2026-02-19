from __future__ import annotations

from sqlmodel import Session

from osiris.modules.inventario.movimiento_inventario.entity import (
    EstadoMovimientoInventario,
    MovimientoInventario,
    MovimientoInventarioDetalle,
)
from osiris.modules.inventario.movimiento_inventario.models import MovimientoInventarioCreate


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
