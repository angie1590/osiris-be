from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func
from sqlmodel import Session, select

from osiris.modules.facturacion.inventario.models import InventarioStock
from osiris.modules.facturacion.reportes.schemas import (
    ReporteInventarioValoracionItemRead,
    ReporteInventarioValoracionRead,
)
from osiris.modules.inventario.producto.entity import Producto


Q4 = Decimal("0.0001")
Q2 = Decimal("0.01")


def q4(value: Decimal | int | str) -> Decimal:
    return Decimal(str(value)).quantize(Q4, rounding=ROUND_HALF_UP)


def q2(value: Decimal | int | str) -> Decimal:
    return Decimal(str(value)).quantize(Q2, rounding=ROUND_HALF_UP)


class ReporteInventarioService:
    @staticmethod
    def _d(value: object, default: str = "0") -> Decimal:
        if value is None:
            return Decimal(default)
        return Decimal(str(value))

    def obtener_valoracion_inventario(self, session: Session) -> ReporteInventarioValoracionRead:
        cantidad_expr = func.coalesce(func.sum(InventarioStock.cantidad_actual), 0)
        valor_expr = func.coalesce(
            func.sum(InventarioStock.cantidad_actual * InventarioStock.costo_promedio_vigente),
            0,
        )

        stmt = (
            select(
                Producto.id,
                Producto.nombre,
                cantidad_expr.label("cantidad_actual"),
                valor_expr.label("valor_total"),
            )
            .select_from(Producto)
            .join(
                InventarioStock,
                (InventarioStock.producto_id == Producto.id) & (InventarioStock.activo.is_(True)),
                isouter=True,
            )
            .where(Producto.activo.is_(True))
            .group_by(Producto.id, Producto.nombre)
            .order_by(Producto.nombre.asc())
        )

        rows = session.exec(stmt).all()

        productos: list[ReporteInventarioValoracionItemRead] = []
        patrimonio_total = Decimal("0.00")
        for producto_id, nombre, cantidad_actual, valor_total in rows:
            cantidad_d = q4(self._d(cantidad_actual))
            valor_d = q2(self._d(valor_total))
            patrimonio_total = q2(patrimonio_total + valor_d)
            costo_promedio = q4(valor_d / cantidad_d) if cantidad_d > Decimal("0") else Decimal("0.0000")

            productos.append(
                ReporteInventarioValoracionItemRead(
                    producto_id=producto_id,
                    nombre=nombre,
                    cantidad_actual=cantidad_d,
                    costo_promedio=costo_promedio,
                    valor_total=valor_d,
                )
            )

        return ReporteInventarioValoracionRead(
            patrimonio_total=q2(patrimonio_total),
            productos=productos,
        )
