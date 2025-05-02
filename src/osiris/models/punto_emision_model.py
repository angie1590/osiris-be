# src/osiris/db/models/punto_emision_modelo.py

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, constr
from uuid import UUID
from typing import Optional


class PuntoEmisionBase(BaseModel):
    codigo: constr(min_length=3, max_length=3)
    descripcion: str
    secuencial_actual: int = Field(1, ge=1)
    empresa_id: UUID
    sucursal_id: Optional[UUID] = None


class PuntoEmisionCrear(PuntoEmisionBase):
    pass


class PuntoEmisionActualizar(BaseModel):
    descripcion: Optional[str] = None
    secuencial_actual: Optional[int] = None
    activo: Optional[bool] = None


class PuntoEmisionRespuesta(PuntoEmisionBase):
    id: UUID
    activo: bool
    fecha_creacion: datetime
    fecha_modificacion: datetime
    usuario_auditoria: Optional[str]

    model_config = ConfigDict(from_attributes=True)
