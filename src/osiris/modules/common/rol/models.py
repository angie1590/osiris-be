# src/modules/common/rol/models.py
from typing import Optional
from uuid import UUID
from sqlmodel import Field
from src.osiris.domain.base_models import BaseTable, AuditMixin, SoftDeleteMixin, BaseOSModel

# DTOs (Pydantic-only)
class RolCreate(BaseOSModel):
    nombre: str
    descripcion: Optional[str] = None
    usuario_auditoria: Optional[str] = None

class RolUpdate(BaseOSModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    usuario_auditoria: Optional[str] = None

class RolRead(BaseOSModel):
    id: UUID
    nombre: str
    descripcion: Optional[str] = None
    activo: bool
