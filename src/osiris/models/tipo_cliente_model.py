from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from pydantic import ConfigDict

class TipoClienteBase(BaseModel):
    nombre: str
    descuento: float = Field(ge=0, le=100)

class TipoClienteCrear(TipoClienteBase):
    pass

class TipoClienteActualizar(BaseModel):
    nombre: Optional[str]
    descuento: Optional[float] = Field(default=None, ge=0, le=100)

class TipoClienteRespuesta(TipoClienteBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)
