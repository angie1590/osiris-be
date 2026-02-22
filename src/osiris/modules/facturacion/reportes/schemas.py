from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class AgrupacionTendencia(str, Enum):
    DIARIA = "DIARIA"
    MENSUAL = "MENSUAL"
    ANUAL = "ANUAL"


class ReporteVentasResumenRead(BaseModel):
    fecha_inicio: date
    fecha_fin: date
    punto_emision_id: UUID | None = None
    subtotal_0: Decimal
    subtotal_12: Decimal
    monto_iva: Decimal
    total: Decimal
    total_ventas: int


class ReporteTopProductoRead(BaseModel):
    producto_id: UUID
    nombre_producto: str
    cantidad_vendida: Decimal
    total_dolares_vendido: Decimal
    ganancia_bruta_estimada: Decimal


class ReporteVentasTendenciaRead(BaseModel):
    periodo: date
    total: Decimal
    total_ventas: int


class ReporteVentasPorVendedorRead(BaseModel):
    usuario_id: UUID | None = None
    vendedor: str
    total_vendido: Decimal
    facturas_emitidas: int
