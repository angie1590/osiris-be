from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Session, select

from osiris.modules.facturacion.core_sri.models import EstadoVenta, Venta, VentaDetalle
from osiris.modules.facturacion.core_sri.all_schemas import ReporteTopProductoRead, ReporteVentasResumenRead, q2
from osiris.modules.facturacion.inventario.models import InventarioStock
from osiris.modules.inventario.producto.entity import Producto


class ReportesVentasService:
    @staticmethod
    def _d(value: object, default: str = "0.00") -> Decimal:
        if value is None:
            return Decimal(default)
        return Decimal(str(value))

    def obtener_resumen_ventas(
        self,
        session: Session,
        *,
        fecha_inicio: date,
        fecha_fin: date,
        punto_emision_id: UUID | None = None,
    ) -> ReporteVentasResumenRead:
        filtros = [
            Venta.activo.is_(True),
            Venta.estado != EstadoVenta.ANULADA,
            Venta.fecha_emision >= fecha_inicio,
            Venta.fecha_emision <= fecha_fin,
        ]
        if punto_emision_id is not None:
            filtros.append(Venta.punto_emision_id == punto_emision_id)

        stmt = select(
            func.coalesce(func.sum(Venta.subtotal_0), 0),
            func.coalesce(func.sum(Venta.subtotal_12), 0),
            func.coalesce(func.sum(Venta.monto_iva), 0),
            func.coalesce(func.sum(Venta.valor_total), 0),
            func.count(Venta.id),
        ).where(*filtros)
        subtotal_0, subtotal_12, monto_iva, total, total_ventas = session.exec(stmt).one()

        return ReporteVentasResumenRead(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            punto_emision_id=punto_emision_id,
            subtotal_0=q2(self._d(subtotal_0)),
            subtotal_12=q2(self._d(subtotal_12)),
            monto_iva=q2(self._d(monto_iva)),
            total=q2(self._d(total)),
            total_ventas=int(total_ventas or 0),
        )

    def obtener_top_productos(
        self,
        session: Session,
        *,
        fecha_inicio: date | None = None,
        fecha_fin: date | None = None,
        punto_emision_id: UUID | None = None,
        limite: int = 10,
    ) -> list[ReporteTopProductoRead]:
        limite_efectivo = max(1, min(limite, 100))
        filtros = [
            Venta.activo.is_(True),
            VentaDetalle.activo.is_(True),
            Producto.activo.is_(True),
            Venta.estado != EstadoVenta.ANULADA,
        ]
        if fecha_inicio is not None:
            filtros.append(Venta.fecha_emision >= fecha_inicio)
        if fecha_fin is not None:
            filtros.append(Venta.fecha_emision <= fecha_fin)
        if punto_emision_id is not None:
            filtros.append(Venta.punto_emision_id == punto_emision_id)

        costo_promedio_subq = (
            select(
                InventarioStock.producto_id.label("producto_id"),
                func.coalesce(func.avg(InventarioStock.costo_promedio_vigente), 0).label("costo_promedio"),
            )
            .where(InventarioStock.activo.is_(True))
            .group_by(InventarioStock.producto_id)
            .subquery()
        )

        ingreso_bruto_expr = func.coalesce(func.sum(VentaDetalle.precio_unitario * VentaDetalle.cantidad), 0)
        cantidad_expr = func.coalesce(func.sum(VentaDetalle.cantidad), 0)

        stmt = (
            select(
                Producto.id,
                Producto.nombre,
                cantidad_expr.label("cantidad_vendida"),
                ingreso_bruto_expr.label("total_dolares_vendido"),
                func.coalesce(costo_promedio_subq.c.costo_promedio, 0).label("costo_promedio"),
            )
            .select_from(VentaDetalle)
            .join(Venta, Venta.id == VentaDetalle.venta_id)
            .join(Producto, Producto.id == VentaDetalle.producto_id)
            .outerjoin(
                costo_promedio_subq,
                costo_promedio_subq.c.producto_id == Producto.id,
            )
            .where(*filtros)
            .group_by(
                Producto.id,
                Producto.nombre,
                costo_promedio_subq.c.costo_promedio,
            )
            .order_by(cantidad_expr.desc())
            .limit(limite_efectivo)
        )

        rows = session.exec(stmt).all()
        items: list[ReporteTopProductoRead] = []
        for producto_id, nombre, cantidad, total_vendido, costo_promedio in rows:
            cantidad_d = self._d(cantidad, default="0.0000")
            total_vendido_d = self._d(total_vendido)
            costo_promedio_d = self._d(costo_promedio, default="0.0000")
            ganancia = q2(total_vendido_d - (costo_promedio_d * cantidad_d))
            items.append(
                ReporteTopProductoRead(
                    producto_id=producto_id,
                    nombre_producto=nombre,
                    cantidad_vendida=Decimal(str(cantidad_d)),
                    total_dolares_vendido=q2(total_vendido_d),
                    ganancia_bruta_estimada=ganancia,
                )
            )
        return items
