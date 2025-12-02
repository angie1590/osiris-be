# src/osiris/modules/inventario/bodega/models.py
from __future__ import annotations

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class BodegaBase(BaseModel):
    codigo_bodega: str
    nombre_bodega: str
    descripcion: Optional[str] = None
    empresa_id: UUID
    sucursal_id: Optional[UUID] = None


class BodegaCreate(BodegaBase):
    pass


class BodegaUpdate(BaseModel):
    codigo_bodega: Optional[str] = None
    nombre_bodega: Optional[str] = None
    descripcion: Optional[str] = None
    sucursal_id: Optional[UUID] = None


class BodegaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    codigo_bodega: str
    nombre_bodega: str
    descripcion: Optional[str] = None
    empresa_id: UUID
    sucursal_id: Optional[UUID] = None
