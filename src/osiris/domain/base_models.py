# src/domain/base_models.py
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field

class BaseOSModel(SQLModel):
    """Modelo base Pydantic-only (no tabla)."""

class AuditMixin(SQLModel):
    creado_en: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    usuario_auditoria: str = Field(default=None)

class SoftDeleteMixin(SQLModel):
    activo: bool = Field(default=True, index=True)

class BaseTable(SQLModel, table=False):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
