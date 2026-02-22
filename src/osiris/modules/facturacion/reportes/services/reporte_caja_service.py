from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_
from sqlmodel import Session, select

from osiris.modules.facturacion.core_sri.schemas import q2
from osiris.modules.facturacion.core_sri.types import EstadoRetencionRecibida
from osiris.modules.facturacion.reportes.schemas import (
    ReporteCajaCierreDiarioRead,
    ReporteCajaCreditoTributarioRead,
    ReporteCajaDineroLiquidoRead,
    ReporteCajaFormaPagoRead,
)
from osiris.modules.facturacion.ventas.models import PagoCxC, RetencionRecibida


class ReporteCajaService:
    @staticmethod
    def _d(value: object, default: str = "0.00") -> Decimal:
        if value is None:
            return Decimal(default)
        return Decimal(str(value))

    def obtener_cierre_diario(
        self,
        session: Session,
        *,
        fecha: date,
        usuario_id: UUID | None = None,
    ) -> ReporteCajaCierreDiarioRead:
        filtros_pagos = [
            PagoCxC.activo.is_(True),
            PagoCxC.fecha == fecha,
        ]
        filtros_retenciones = [
            RetencionRecibida.activo.is_(True),
            RetencionRecibida.estado == EstadoRetencionRecibida.APLICADA,
            RetencionRecibida.fecha_emision == fecha,
        ]
        if usuario_id is not None:
            usuario_id_str = str(usuario_id)
            filtros_pagos.append(
                or_(
                    PagoCxC.created_by == usuario_id_str,
                    PagoCxC.usuario_auditoria == usuario_id_str,
                )
            )
            filtros_retenciones.append(
                or_(
                    RetencionRecibida.created_by == usuario_id_str,
                    RetencionRecibida.usuario_auditoria == usuario_id_str,
                )
            )

        pagos_stmt = (
            select(
                PagoCxC.forma_pago_sri,
                func.coalesce(func.sum(PagoCxC.monto), 0).label("monto"),
            )
            .where(*filtros_pagos)
            .group_by(PagoCxC.forma_pago_sri)
            .order_by(PagoCxC.forma_pago_sri.asc())
        )
        pagos_rows = session.exec(pagos_stmt).all()
        pagos = [
            ReporteCajaFormaPagoRead(
                forma_pago_sri=forma_pago,
                monto=q2(self._d(monto)),
            )
            for forma_pago, monto in pagos_rows
        ]
        total_dinero = q2(sum((pago.monto for pago in pagos), Decimal("0.00")))

        retenciones_stmt = select(func.coalesce(func.sum(RetencionRecibida.total_retenido), 0)).where(
            *filtros_retenciones
        )
        total_retenciones = q2(self._d(session.exec(retenciones_stmt).one()))

        return ReporteCajaCierreDiarioRead(
            fecha=fecha,
            usuario_id=usuario_id,
            dinero_liquido=ReporteCajaDineroLiquidoRead(
                total=total_dinero,
                por_forma_pago=pagos,
            ),
            credito_tributario=ReporteCajaCreditoTributarioRead(
                total_retenciones=total_retenciones,
            ),
        )
