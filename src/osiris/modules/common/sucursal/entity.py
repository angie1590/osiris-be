from __future__ import annotations
from typing import Optional
from uuid import UUID
from sqlmodel import Field

from src.osiris.domain.base_models import BaseTable, AuditMixin, SoftDeleteMixin


class Sucursal(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_sucursal"

    codigo: str = Field(index=True, nullable=False, max_length=3)
    nombre: str = Field(nullable=False, max_length=50)
    direccion: str = Field(nullable=False, max_length=100)
    telefono: Optional[str] = Field(default=None, max_length=15)

    # FK a empresa (forma simple y consistente)
    empresa_id: UUID = Field(
        foreign_key="tbl_empresa.id",
        nullable=False,
    )
