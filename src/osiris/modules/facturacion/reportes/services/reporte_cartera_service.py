from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func
from sqlmodel import Session, select

from osiris.modules.facturacion.compras.models import Compra, CuentaPorPagar
from osiris.modules.facturacion.core_sri.schemas import q2
from osiris.modules.facturacion.core_sri.types import EstadoCuentaPorCobrar, EstadoCuentaPorPagar
from osiris.modules.facturacion.reportes.schemas import (
    ReporteCarteraCobrarItemRead,
    ReporteCarteraPagarItemRead,
)
from osiris.modules.facturacion.ventas.models import CuentaPorCobrar, Venta


class ReporteCarteraService:
    @staticmethod
    def _d(value: object, default: str = "0.00") -> Decimal:
        if value is None:
            return Decimal(default)
        return Decimal(str(value))

    def obtener_cartera_cobrar(self, session: Session) -> list[ReporteCarteraCobrarItemRead]:
        stmt = (
            select(
                Venta.cliente_id,
                func.coalesce(func.sum(CuentaPorCobrar.saldo_pendiente), 0).label("saldo"),
            )
            .select_from(CuentaPorCobrar)
            .join(Venta, Venta.id == CuentaPorCobrar.venta_id)
            .where(
                CuentaPorCobrar.activo.is_(True),
                Venta.activo.is_(True),
                CuentaPorCobrar.saldo_pendiente > Decimal("0"),
                CuentaPorCobrar.estado.in_(
                    [EstadoCuentaPorCobrar.PENDIENTE, EstadoCuentaPorCobrar.PARCIAL]
                ),
                Venta.cliente_id.is_not(None),
            )
            .group_by(Venta.cliente_id)
            .order_by(func.sum(CuentaPorCobrar.saldo_pendiente).desc())
        )
        rows = session.exec(stmt).all()
        return [
            ReporteCarteraCobrarItemRead(
                cliente_id=cliente_id,
                saldo_pendiente=q2(self._d(saldo)),
            )
            for cliente_id, saldo in rows
        ]

    def obtener_cartera_pagar(self, session: Session) -> list[ReporteCarteraPagarItemRead]:
        stmt = (
            select(
                Compra.proveedor_id,
                func.coalesce(func.sum(CuentaPorPagar.saldo_pendiente), 0).label("saldo"),
            )
            .select_from(CuentaPorPagar)
            .join(Compra, Compra.id == CuentaPorPagar.compra_id)
            .where(
                CuentaPorPagar.activo.is_(True),
                Compra.activo.is_(True),
                CuentaPorPagar.saldo_pendiente > Decimal("0"),
                CuentaPorPagar.estado.in_(
                    [EstadoCuentaPorPagar.PENDIENTE, EstadoCuentaPorPagar.PARCIAL]
                ),
            )
            .group_by(Compra.proveedor_id)
            .order_by(func.sum(CuentaPorPagar.saldo_pendiente).desc())
        )
        rows = session.exec(stmt).all()
        return [
            ReporteCarteraPagarItemRead(
                proveedor_id=proveedor_id,
                saldo_pendiente=q2(self._d(saldo)),
            )
            for proveedor_id, saldo in rows
        ]
