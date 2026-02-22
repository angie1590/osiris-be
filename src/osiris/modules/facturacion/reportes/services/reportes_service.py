from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import String, cast, func
from sqlmodel import Session, select

from osiris.modules.facturacion.core_sri.models import EstadoVenta, Venta, VentaDetalle
from osiris.modules.facturacion.core_sri.schemas import q2
from osiris.modules.facturacion.inventario.models import InventarioStock
from osiris.modules.facturacion.reportes.schemas import (
    AgrupacionTendencia,
    ReporteTopProductoRead,
    ReporteVentasPorVendedorRead,
    ReporteVentasResumenRead,
    ReporteVentasTendenciaRead,
)
from osiris.modules.common.punto_emision.entity import PuntoEmision
from osiris.modules.common.usuario.entity import Usuario
from osiris.modules.inventario.producto.entity import Producto


class ReportesVentasService:
    @staticmethod
    def _d(value: object, default: str = "0.00") -> Decimal:
        if value is None:
            return Decimal(default)
        return Decimal(str(value))

    @staticmethod
    def _to_period_date(value: object) -> date:
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            return date.fromisoformat(value[:10])
        raise ValueError("No se pudo convertir el periodo de tendencia a fecha")

    @staticmethod
    def _bucket_expr(session: Session, agrupacion: AgrupacionTendencia):
        bind = session.get_bind()
        dialect = bind.dialect.name if bind is not None else ""
        if dialect == "postgresql":
            if agrupacion == AgrupacionTendencia.ANUAL:
                return func.date_trunc("year", Venta.fecha_emision)
            if agrupacion == AgrupacionTendencia.MENSUAL:
                return func.date_trunc("month", Venta.fecha_emision)
            return func.date_trunc("day", Venta.fecha_emision)
        if agrupacion == AgrupacionTendencia.ANUAL:
            return func.strftime("%Y-01-01", Venta.fecha_emision)
        if agrupacion == AgrupacionTendencia.MENSUAL:
            return func.strftime("%Y-%m-01", Venta.fecha_emision)
        return func.date(Venta.fecha_emision)

    def obtener_resumen_ventas(
        self,
        session: Session,
        *,
        fecha_inicio: date,
        fecha_fin: date,
        punto_emision_id: UUID | None = None,
        sucursal_id: UUID | None = None,
    ) -> ReporteVentasResumenRead:
        filtros = [
            Venta.activo.is_(True),
            Venta.estado != EstadoVenta.ANULADA,
            Venta.fecha_emision >= fecha_inicio,
            Venta.fecha_emision <= fecha_fin,
        ]
        if punto_emision_id is not None:
            filtros.append(Venta.punto_emision_id == punto_emision_id)
        if sucursal_id is not None:
            filtros.append(PuntoEmision.sucursal_id == sucursal_id)

        stmt = select(
            func.coalesce(func.sum(Venta.subtotal_0), 0),
            func.coalesce(func.sum(Venta.subtotal_12), 0),
            func.coalesce(func.sum(Venta.monto_iva), 0),
            func.coalesce(func.sum(Venta.valor_total), 0),
            func.count(Venta.id),
        ).select_from(Venta)
        if sucursal_id is not None:
            stmt = stmt.join(PuntoEmision, PuntoEmision.id == Venta.punto_emision_id)
        stmt = stmt.where(*filtros)
        subtotal_0, subtotal_12, monto_iva, total, total_ventas = session.exec(stmt).one()

        return ReporteVentasResumenRead(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            punto_emision_id=punto_emision_id,
            sucursal_id=sucursal_id,
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

    def obtener_tendencias_ventas(
        self,
        session: Session,
        *,
        fecha_inicio: date,
        fecha_fin: date,
        agrupacion: AgrupacionTendencia,
    ) -> list[ReporteVentasTendenciaRead]:
        bucket = self._bucket_expr(session, agrupacion)
        stmt = (
            select(
                bucket.label("periodo"),
                func.coalesce(func.sum(Venta.valor_total), 0).label("total"),
                func.count(Venta.id).label("total_ventas"),
            )
            .where(
                Venta.activo.is_(True),
                Venta.estado != EstadoVenta.ANULADA,
                Venta.fecha_emision >= fecha_inicio,
                Venta.fecha_emision <= fecha_fin,
            )
            .group_by(bucket)
            .order_by(bucket.asc())
        )
        rows = session.exec(stmt).all()
        return [
            ReporteVentasTendenciaRead(
                periodo=self._to_period_date(periodo),
                total=q2(self._d(total)),
                total_ventas=int(total_ventas or 0),
            )
            for periodo, total, total_ventas in rows
        ]

    def obtener_ventas_por_vendedor(
        self,
        session: Session,
        *,
        fecha_inicio: date | None = None,
        fecha_fin: date | None = None,
    ) -> list[ReporteVentasPorVendedorRead]:
        filtros = [
            Venta.activo.is_(True),
            Venta.estado != EstadoVenta.ANULADA,
        ]
        if fecha_inicio is not None:
            filtros.append(Venta.fecha_emision >= fecha_inicio)
        if fecha_fin is not None:
            filtros.append(Venta.fecha_emision <= fecha_fin)

        join_cond = cast(Usuario.id, String) == Venta.created_by
        vendedor_expr = func.coalesce(Usuario.username, Venta.created_by, "SIN_USUARIO")

        stmt = (
            select(
                Usuario.id.label("usuario_id"),
                vendedor_expr.label("vendedor"),
                func.coalesce(func.sum(Venta.valor_total), 0).label("total_vendido"),
                func.count(Venta.id).label("facturas_emitidas"),
            )
            .select_from(Venta)
            .outerjoin(Usuario, join_cond)
            .where(*filtros)
            .group_by(Usuario.id, vendedor_expr)
            .order_by(func.sum(Venta.valor_total).desc(), vendedor_expr.asc())
        )
        rows = session.exec(stmt).all()
        return [
            ReporteVentasPorVendedorRead(
                usuario_id=usuario_id,
                vendedor=str(vendedor),
                total_vendido=q2(self._d(total_vendido)),
                facturas_emitidas=int(facturas_emitidas or 0),
            )
            for usuario_id, vendedor, total_vendido, facturas_emitidas in rows
        ]
