from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict

class ClienteBase(BaseModel):
    tipo_cliente_id: UUID

class ClienteCrear(ClienteBase):
    persona_id: UUID
    usuario_auditoria: str

class ClienteActualizar(BaseModel):
    tipo_cliente_id: Optional[UUID] = None
    activo: Optional[bool] = True
    usuario_auditoria: str

class ClienteRespuesta(ClienteBase):
    id: UUID
    activo: bool
    fecha_creacion: datetime
    fecha_modificacion: datetime
    usuario_auditoria: Optional[str]

    model_config = ConfigDict(from_attributes=True)
