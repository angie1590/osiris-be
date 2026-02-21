from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from osiris.modules.facturacion.core_sri.models import CuentaPorPagar, EstadoCuentaPorPagar, PagoCxP
from osiris.modules.facturacion.core_sri.all_schemas import PagoCxPCreate, q2


class CuentaPorPagarService:
    def registrar_pago_cxp(
        self,
        session: Session,
        cuenta_por_pagar_id: UUID,
        payload: PagoCxPCreate,
        *,
        commit: bool = True,
        rollback_on_error: bool = True,
    ) -> PagoCxP:
        try:
            cxp = session.exec(
                select(CuentaPorPagar)
                .where(
                    CuentaPorPagar.id == cuenta_por_pagar_id,
                    CuentaPorPagar.activo.is_(True),
                )
                .with_for_update()
            ).one_or_none()
            if not cxp:
                raise HTTPException(status_code=404, detail="Cuenta por pagar no encontrada")

            if cxp.estado == EstadoCuentaPorPagar.ANULADA:
                raise ValueError("No se puede registrar pagos en una cuenta por pagar ANULADA.")

            monto_pago = q2(payload.monto)
            saldo_actual = q2(cxp.saldo_pendiente)
            if monto_pago > saldo_actual:
                raise HTTPException(
                    status_code=400,
                    detail="El monto del pago no puede ser mayor al saldo pendiente.",
                )

            pago = PagoCxP(
                cuenta_por_pagar_id=cxp.id,
                monto=monto_pago,
                fecha=payload.fecha,
                forma_pago=payload.forma_pago,
                usuario_auditoria=payload.usuario_auditoria,
                activo=True,
            )
            session.add(pago)

            cxp.pagos_acumulados = q2(cxp.pagos_acumulados + monto_pago)
            nuevo_saldo = q2(cxp.valor_total_factura - cxp.valor_retenido - cxp.pagos_acumulados)
            if nuevo_saldo < Decimal("0.00"):
                raise ValueError("Saldo pendiente invalido luego de aplicar el pago.")

            cxp.saldo_pendiente = nuevo_saldo
            if nuevo_saldo == Decimal("0.00"):
                cxp.estado = EstadoCuentaPorPagar.PAGADA
            elif cxp.pagos_acumulados > Decimal("0.00"):
                cxp.estado = EstadoCuentaPorPagar.PARCIAL
            else:
                cxp.estado = EstadoCuentaPorPagar.PENDIENTE
            session.add(cxp)

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
