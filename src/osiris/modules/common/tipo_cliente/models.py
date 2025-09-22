from __future__ import annotations
from typing import Optional
from uuid import UUID

from pydantic import Field
from src.osiris.domain.base_models import BaseOSModel


class TipoClienteBase(BaseOSModel):
    nombre: str
    descuento: int = Field(ge=0, le=100)


class TipoClienteCreate(TipoClienteBase):
    usuario_auditoria: str
    pass


class TipoClienteUpdate(BaseOSModel):
    nombre: Optional[str] = None
    descuento: Optional[float] = Field(default=None, ge=0, le=100)
    usuario_auditoria: Optional[str] = None


class TipoClienteRead(TipoClienteBase):
    id: UUID
