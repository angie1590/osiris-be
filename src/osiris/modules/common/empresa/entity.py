# src/osiris/modules/common/empresa/entity.py
from __future__ import annotations
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, String, ForeignKey
from sqlmodel import SQLModel, Field, Relationship

class Empresa(SQLModel, table=True):
    __tablename__ = "tbl_empresa"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)

    razon_social: str = Field(nullable=False)
    nombre_comercial: Optional[str] = Field(default=None)
    ruc: str = Field(index=True, nullable=False)
    direccion_matriz: str = Field(nullable=False)
    telefono: Optional[str] = Field(default=None)
    codigo_establecimiento: Optional[str] = Field(default=None)
    obligado_contabilidad: bool = Field(default=False)

    # Auditoría / estado
    activo: bool = Field(default=True, index=True)
    usuario_auditoria: str = Field(nullable=False)
    creado_en: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # FK -> aux_tipo_contribuyente.codigo (PK)
    tipo_contribuyente_id: str = Field(
        sa_column=Column(
            String(2),
            ForeignKey("aux_tipo_contribuyente.codigo", ondelete="RESTRICT"),
            nullable=False,
        )
    )
