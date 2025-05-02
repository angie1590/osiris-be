from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict

class RolBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class RolCrear(RolBase):
    usuario_auditoria: str

class RolActualizar(BaseModel):
    descripcion: Optional[str] = None
    activo: Optional[bool] = True
    usuario_auditoria: str

class RolRespuesta(RolBase):
    id: UUID
    activo: bool
    fecha_creacion: datetime
    fecha_modificacion: datetime
    usuario_auditoria: Optional[str]

    model_config = ConfigDict(from_attributes=True)
