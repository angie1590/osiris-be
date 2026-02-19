from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from osiris.modules.inventario.movimiento_inventario.entity import (
    EstadoMovimientoInventario,
    TipoMovimientoInventario,
)


class MovimientoInventarioDetalleCreate(BaseModel):
    producto_id: UUID
    cantidad: Decimal = Field(..., gt=Decimal("0"))
    costo_unitario: Decimal = Field(..., ge=Decimal("0"))

    @field_validator("cantidad")
    @classmethod
    def validar_cantidad_positiva(cls, value: Decimal) -> Decimal:
        if Decimal(str(value)) <= Decimal("0"):
            raise ValueError("La cantidad debe ser mayor a 0.")
        return Decimal(str(value))


class MovimientoInventarioCreate(BaseModel):
    fecha: date = Field(default_factory=date.today)
    bodega_id: UUID
    tipo_movimiento: TipoMovimientoInventario
    estado: EstadoMovimientoInventario = EstadoMovimientoInventario.BORRADOR
    referencia_documento: str | None = Field(default=None, max_length=120)
    usuario_auditoria: str | None = None
    detalles: list[MovimientoInventarioDetalleCreate] = Field(..., min_length=1)


class MovimientoInventarioDetalleRead(BaseModel):
    id: UUID
    movimiento_inventario_id: UUID
    producto_id: UUID
    cantidad: Decimal
    costo_unitario: Decimal


class MovimientoInventarioRead(BaseModel):
    id: UUID
    fecha: date
    bodega_id: UUID
    tipo_movimiento: TipoMovimientoInventario
    estado: EstadoMovimientoInventario
    referencia_documento: str | None = None
    detalles: list[MovimientoInventarioDetalleRead]
