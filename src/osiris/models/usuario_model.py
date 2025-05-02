from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from pydantic import ConfigDict

class UsuarioBase(BaseModel):
    username: str
    rol_id: UUID

class UsuarioCrear(UsuarioBase):
    password: str = Field(min_length=8)
    persona_id: UUID
    usuario_auditoria: str

class UsuarioActualizar(BaseModel):
    rol_id: Optional[UUID] = None
    password: Optional[str] = Field(default=None, min_length=8)
    requiere_cambio_password: Optional[bool] = None
    activo: Optional[bool] = None
    usuario_auditoria: str

class UsuarioRespuesta(UsuarioBase):
    id: UUID
    persona_id: UUID
    requiere_cambio_password: bool
    activo: bool
    usuario_auditoria: Optional[str]

    model_config = ConfigDict(from_attributes=True)
