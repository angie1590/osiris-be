from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict

class ProveedorPersonaBase(BaseModel):
    tipo_contribuyente_id: str = Field(min_length=2, max_length=2)
    nombre_comercial: Optional[str] = None

class ProveedorPersonaCrear(ProveedorPersonaBase):
    id: UUID
    usuario_auditoria: str

class ProveedorPersonaActualizar(BaseModel):
    tipo_contribuyente_id: Optional[str] = None
    nombre_comercial: Optional[str] = None
    activo: Optional[bool] = True
    usuario_auditoria: str

class ProveedorPersonaRespuesta(ProveedorPersonaBase):
    id: UUID
    activo: bool
    fecha_creacion: datetime
    fecha_modificacion: datetime
    usuario_auditoria: Optional[str]

    model_config = ConfigDict(from_attributes=True)
