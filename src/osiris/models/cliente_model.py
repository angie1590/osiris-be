from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional
from datetime import datetime

class ClienteBase(BaseModel):
    tipo_cliente_id: UUID

class ClienteCrear(ClienteBase):
    id: UUID  # <- ahora representa directamente el ID de la persona
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