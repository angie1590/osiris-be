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


class ReporteImpuestoAgrupadoRead(BaseModel):
    codigo_sri: str
    total_retenido: Decimal


class ReportePre104BloqueRead(BaseModel):
    base_0: Decimal
    base_iva: Decimal
    monto_iva: Decimal
    total: Decimal
    total_documentos: int


class ReporteImpuestosMensualRead(BaseModel):
    mes: int
    anio: int
    ventas: ReportePre104BloqueRead
    compras: ReportePre104BloqueRead
    retenciones_emitidas: dict[str, Decimal]
    retenciones_recibidas: dict[str, Decimal]


class ReporteInventarioValoracionItemRead(BaseModel):
    producto_id: UUID
    nombre: str
    cantidad_actual: Decimal
    costo_promedio: Decimal
    valor_total: Decimal


class ReporteInventarioValoracionRead(BaseModel):
    patrimonio_total: Decimal
    productos: list[ReporteInventarioValoracionItemRead]


class ReporteCarteraCobrarItemRead(BaseModel):
    cliente_id: UUID
    saldo_pendiente: Decimal


class ReporteCarteraPagarItemRead(BaseModel):
    proveedor_id: UUID
    saldo_pendiente: Decimal
