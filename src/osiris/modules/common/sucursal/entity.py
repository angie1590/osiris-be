from __future__ import annotations
from typing import Optional
from uuid import UUID
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlmodel import Field

from osiris.domain.base_models import BaseTable, AuditMixin, SoftDeleteMixin


class Sucursal(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_sucursal"
    __table_args__ = (
        UniqueConstraint("empresa_id", "codigo", name="uq_sucursal_empresa_codigo"),
        CheckConstraint(
            "(codigo = '001' AND es_matriz = true) OR (codigo != '001' AND es_matriz = false)",
            name="ck_sucursal_matriz_codigo",
        ),
    )

    codigo: str = Field(index=True, nullable=False, max_length=3)
    nombre: str = Field(nullable=False, max_length=50)
    direccion: str = Field(nullable=False, max_length=100)
    telefono: Optional[str] = Field(default=None, max_length=15)
    es_matriz: bool = Field(default=False, nullable=False)

    # FK a empresa (forma simple y consistente)
    empresa_id: UUID = Field(
        foreign_key="tbl_empresa.id",
        nullable=False,
    )
