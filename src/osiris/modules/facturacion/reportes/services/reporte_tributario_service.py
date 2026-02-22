from __future__ import annotations

from decimal import Decimal

from sqlalchemy import case, func
from sqlmodel import Session, select

from osiris.modules.facturacion.compras.models import Compra, Retencion, RetencionDetalle
from osiris.modules.facturacion.core_sri.types import (
    EstadoCompra,
    EstadoRetencion,
    EstadoRetencionRecibida,
    EstadoVenta,
    TipoRetencionSRI,
)
from osiris.modules.facturacion.reportes.schemas import (
    ReportePre104BloqueRead,
    ReporteImpuestosMensualRead,
)
from osiris.modules.facturacion.ventas.models import RetencionRecibida, RetencionRecibidaDetalle, Venta
from osiris.modules.facturacion.core_sri.schemas import q2


class ReporteTributarioService:
    @staticmethod
    def _d(value: object, default: str = "0.00") -> Decimal:
        if value is None:
            return Decimal(default)
        return Decimal(str(value))

    @staticmethod
    def _period_filters(session: Session, field, mes: int, anio: int):
        bind = session.get_bind()
        dialect = bind.dialect.name if bind is not None else ""
        if dialect == "postgresql":
            return [
                func.extract("month", field) == mes,
                func.extract("year", field) == anio,
            ]
        return [
            func.strftime("%m", field) == f"{mes:02d}",
            func.strftime("%Y", field) == str(anio),
        ]

    def obtener_reporte_mensual_impuestos(
        self,
        session: Session,
        *,
        mes: int,
        anio: int,
    ) -> ReporteImpuestosMensualRead:
        ventas_filtros = [
            Venta.activo.is_(True),
            Venta.estado != EstadoVenta.ANULADA,
            *self._period_filters(session, Venta.fecha_emision, mes, anio),
        ]
        ventas_stmt = select(
            func.coalesce(func.sum(Venta.subtotal_0), 0),
            func.coalesce(func.sum(Venta.subtotal_12), 0),
            func.coalesce(func.sum(Venta.subtotal_15), 0),
            func.coalesce(func.sum(Venta.monto_iva), 0),
            func.coalesce(func.sum(Venta.valor_total), 0),
            func.count(Venta.id),
        ).where(*ventas_filtros)
        (
            ventas_subtotal_0,
            ventas_subtotal_12,
            ventas_subtotal_15,
            ventas_monto_iva,
            ventas_total,
            ventas_count,
        ) = session.exec(ventas_stmt).one()
        ventas = ReportePre104BloqueRead(
            base_0=q2(self._d(ventas_subtotal_0)),
            base_iva=q2(self._d(ventas_subtotal_12) + self._d(ventas_subtotal_15)),
            monto_iva=q2(self._d(ventas_monto_iva)),
            total=q2(self._d(ventas_total)),
            total_documentos=int(ventas_count or 0),
        )

        compras_filtros = [
            Compra.activo.is_(True),
            Compra.estado != EstadoCompra.ANULADA,
            *self._period_filters(session, Compra.fecha_emision, mes, anio),
        ]
        compras_stmt = select(
            func.coalesce(func.sum(Compra.subtotal_0), 0),
            func.coalesce(func.sum(Compra.subtotal_12), 0),
            func.coalesce(func.sum(Compra.subtotal_15), 0),
            func.coalesce(func.sum(Compra.monto_iva), 0),
            func.coalesce(func.sum(Compra.valor_total), 0),
            func.count(Compra.id),
        ).where(*compras_filtros)
        (
            subtotal_0,
            subtotal_12,
            subtotal_15,
            monto_iva,
            total,
            total_documentos,
        ) = session.exec(compras_stmt).one()

        compras = ReportePre104BloqueRead(
            base_0=q2(self._d(subtotal_0)),
            base_iva=q2(self._d(subtotal_12) + self._d(subtotal_15)),
            monto_iva=q2(self._d(monto_iva)),
            total=q2(self._d(total)),
            total_documentos=int(total_documentos or 0),
        )

        codigo_pasivo_expr = case(
            (RetencionDetalle.tipo == TipoRetencionSRI.RENTA, "1"),
            (RetencionDetalle.tipo == TipoRetencionSRI.IVA, "2"),
            else_=RetencionDetalle.codigo_retencion_sri,
        )
        pasivo_stmt = (
            select(
                codigo_pasivo_expr.label("codigo_sri"),
                func.coalesce(func.sum(RetencionDetalle.valor_retenido), 0).label("total"),
            )
            .select_from(RetencionDetalle)
            .join(Retencion, Retencion.id == RetencionDetalle.retencion_id)
            .join(Compra, Compra.id == Retencion.compra_id)
            .where(
                RetencionDetalle.activo.is_(True),
                Retencion.activo.is_(True),
                Compra.activo.is_(True),
                Retencion.estado == EstadoRetencion.EMITIDA,
                Compra.estado != EstadoCompra.ANULADA,
                *self._period_filters(session, Compra.fecha_emision, mes, anio),
            )
            .group_by(codigo_pasivo_expr)
            .order_by(codigo_pasivo_expr.asc())
        )
        pasivo_rows = session.exec(pasivo_stmt).all()
        pasivo = {str(codigo_sri): q2(self._d(total_retenido)) for codigo_sri, total_retenido in pasivo_rows}

        credito_stmt = (
            select(
                RetencionRecibidaDetalle.codigo_impuesto_sri.label("codigo_sri"),
                func.coalesce(func.sum(RetencionRecibidaDetalle.valor_retenido), 0).label("total"),
            )
            .select_from(RetencionRecibidaDetalle)
            .join(
                RetencionRecibida,
                RetencionRecibida.id == RetencionRecibidaDetalle.retencion_recibida_id,
            )
            .where(
                RetencionRecibidaDetalle.activo.is_(True),
                RetencionRecibida.activo.is_(True),
                RetencionRecibida.estado == EstadoRetencionRecibida.APLICADA,
                *self._period_filters(session, RetencionRecibida.fecha_emision, mes, anio),
            )
            .group_by(RetencionRecibidaDetalle.codigo_impuesto_sri)
            .order_by(RetencionRecibidaDetalle.codigo_impuesto_sri.asc())
        )
        credito_rows = session.exec(credito_stmt).all()
        credito = {str(codigo_sri): q2(self._d(total_retenido)) for codigo_sri, total_retenido in credito_rows}

        return ReporteImpuestosMensualRead(
            mes=mes,
            anio=anio,
            ventas=ventas,
            compras=compras,
            retenciones_emitidas=pasivo,
            retenciones_recibidas=credito,
        )
