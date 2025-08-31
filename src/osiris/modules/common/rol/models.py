# src/modules/common/rol/models.py
from typing import Optional
from uuid import UUID
from sqlmodel import Field
from src.osiris.domain.base_models import BaseTable, AuditMixin, SoftDeleteMixin, BaseOSModel

class Rol(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_rol"
    nombre: str = Field(index=True, nullable=False, unique=True, max_length=120)
    descripcion: Optional[str] = Field(default=None, max_length=255)

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
