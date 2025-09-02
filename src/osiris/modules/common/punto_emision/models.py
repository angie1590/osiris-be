from __future__ import annotations
from typing import Optional, Annotated
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, StringConstraints, Field

Codigo3 = Annotated[str, StringConstraints(min_length=3, max_length=3)]

class PuntoEmisionBase(BaseModel):
    codigo: Codigo3
    descripcion: str
    secuencial_actual: int = Field(1, ge=1)
    usuario_auditoria: str
    empresa_id: UUID
    sucursal_id: Optional[UUID] = None

class PuntoEmisionCreate(PuntoEmisionBase):
    pass

class PuntoEmisionUpdate(BaseModel):
    descripcion: Optional[str] = None
    secuencial_actual: Optional[int] = None
    usuario_auditoria: Optional[str] = None
    activo: Optional[bool] = None

class PuntoEmisionRead(PuntoEmisionBase):
    id: UUID
    activo: bool
    creado_en: datetime
    actualizado_en: datetime
    usuario_auditoria: Optional[str]

    model_config = ConfigDict(from_attributes=True)
