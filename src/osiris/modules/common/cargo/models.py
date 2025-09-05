# src/modules/common/rol/models.py
from typing import Optional
from uuid import UUID
from sqlmodel import Field
from src.osiris.domain.base_models import BaseTable, AuditMixin, SoftDeleteMixin, BaseOSModel

# DTOs (Pydantic-only)
class CargoCreate(BaseOSModel):
    nombre: str
    usuario_auditoria: Optional[str] = None

class CargoUpdate(BaseOSModel):
    nombre: Optional[str] = None
    usuario_auditoria: Optional[str] = None

class CargoRead(BaseOSModel):
    id: UUID
    nombre: str
    activo: bool
