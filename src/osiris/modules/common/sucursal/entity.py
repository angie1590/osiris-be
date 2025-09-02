from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlmodel import SQLModel, Field


class Sucursal(SQLModel, table=True):
    __tablename__ = "tbl_sucursal"

    # PK
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)

    # Campos de dominio
    codigo: str = Field(sa_column=Column(String(3), nullable=False))
    nombre: str = Field(nullable=False)
    direccion: str = Field(nullable=False)
    telefono: Optional[str] = Field(default=None)
    activo: bool = Field(default=True, nullable=False)

    # Auditoría
    fecha_creacion: datetime = Field(default_factory=datetime.now, nullable=False)
    fecha_modificacion: datetime = Field(
        default_factory=datetime.now, nullable=False
    )
    usuario_auditoria: str = Field(nullable=False)

    # FK a empresa (sin relationship para evitar ciclos)
    empresa_id: UUID = Field(
        sa_column=Column(
            SQLModel.metadata.schema and UUID,
            ForeignKey("tbl_empresa.id"),
            nullable=False,
        )
    )
