from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Column
from sqlmodel import Field

from osiris.domain.base_models import BaseTable


class AuditLog(BaseTable, table=True):
    __tablename__ = "audit_log"

    entidad: str = Field(nullable=False, max_length=100, index=True)
    entidad_id: UUID = Field(nullable=False, index=True)
    accion: str = Field(nullable=False, max_length=20, default="UPDATE")
    estado_anterior: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    estado_nuevo: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    before_json: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    after_json: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    usuario_auditoria: str | None = Field(default=None, max_length=255)
    creado_en: datetime = Field(default_factory=datetime.utcnow, nullable=False)
