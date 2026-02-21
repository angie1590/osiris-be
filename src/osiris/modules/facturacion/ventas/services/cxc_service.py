from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from osiris.modules.facturacion.core_sri.models import (
    CuentaPorCobrar,
    EstadoCuentaPorCobrar,
    PagoCxC,
)
from osiris.modules.facturacion.core_sri.all_schemas import PagoCxCCreate, q2


class CuentaPorCobrarService:
    @staticmethod
    def _recalcular_saldo_y_estado(cxc: CuentaPorCobrar) -> None:
        nuevo_saldo = q2(cxc.valor_total_factura - cxc.valor_retenido - cxc.pagos_acumulados)
        if nuevo_saldo < Decimal("0.00"):
            raise ValueError("La retención supera el saldo de la factura")

        cxc.saldo_pendiente = nuevo_saldo
        if nuevo_saldo == Decimal("0.00"):
            cxc.estado = EstadoCuentaPorCobrar.PAGADA
        elif q2(cxc.pagos_acumulados) > Decimal("0.00") or q2(cxc.valor_retenido) > Decimal("0.00"):
            cxc.estado = EstadoCuentaPorCobrar.PARCIAL
        else:
            cxc.estado = EstadoCuentaPorCobrar.PENDIENTE

    @staticmethod
    def aplicar_retencion_en_cxc(cxc: CuentaPorCobrar, valor_aplicar: Decimal) -> None:
        valor = q2(valor_aplicar)
        if valor > q2(cxc.saldo_pendiente):
            raise ValueError("La retención supera el saldo de la factura")

        cxc.valor_retenido = q2(cxc.valor_retenido + valor)
        CuentaPorCobrarService._recalcular_saldo_y_estado(cxc)

    @staticmethod
    def revertir_retencion_en_cxc(cxc: CuentaPorCobrar, valor_reverso: Decimal) -> None:
        valor = q2(valor_reverso)
        if valor > q2(cxc.valor_retenido):
            raise ValueError("La retención supera el saldo de la factura")

        cxc.valor_retenido = q2(cxc.valor_retenido - valor)
        CuentaPorCobrarService._recalcular_saldo_y_estado(cxc)

    @staticmethod
    def aplicar_pago_en_cxc(cxc: CuentaPorCobrar, monto_pago: Decimal) -> None:
        monto = q2(monto_pago)
        if monto > q2(cxc.saldo_pendiente):
            raise HTTPException(
                status_code=400,
                detail="El monto del pago no puede ser mayor al saldo pendiente.",
            )

        cxc.pagos_acumulados = q2(cxc.pagos_acumulados + monto)
        CuentaPorCobrarService._recalcular_saldo_y_estado(cxc)

    def obtener_cxc_por_venta(self, session: Session, venta_id: UUID) -> CuentaPorCobrar:
        cxc = session.exec(
            select(CuentaPorCobrar).where(
                CuentaPorCobrar.venta_id == venta_id,
                CuentaPorCobrar.activo.is_(True),
            )
        ).one_or_none()
        if not cxc:
            raise HTTPException(status_code=404, detail="Cuenta por cobrar no encontrada para la venta")
        return cxc

    def registrar_pago_cxc(
        self,
        session: Session,
        cuenta_por_cobrar_id: UUID,
        payload: PagoCxCCreate,
        *,
        commit: bool = True,
        rollback_on_error: bool = True,
    ) -> PagoCxC:
        try:
            cxc = session.exec(
                select(CuentaPorCobrar)
                .where(
                    CuentaPorCobrar.id == cuenta_por_cobrar_id,
                    CuentaPorCobrar.activo.is_(True),
                )
                .with_for_update()
            ).one_or_none()
            if not cxc:
                raise HTTPException(status_code=404, detail="Cuenta por cobrar no encontrada")

            if cxc.estado == EstadoCuentaPorCobrar.ANULADA:
                raise HTTPException(status_code=400, detail="No se puede registrar pagos en una CxC ANULADA.")

            self.aplicar_pago_en_cxc(cxc, payload.monto)
            cxc.usuario_auditoria = payload.usuario_auditoria

            pago = PagoCxC(
                cuenta_por_cobrar_id=cxc.id,
                monto=q2(payload.monto),
                fecha=payload.fecha,
                forma_pago_sri=payload.forma_pago_sri,
                usuario_auditoria=payload.usuario_auditoria,
                activo=True,
            )
            session.add(pago)
            session.add(cxc)

            if commit:
                session.commit()
                session.refresh(pago)
            else:
                session.flush()
            return pago
        except Exception:
            if rollback_on_error:
                session.rollback()
            raise
