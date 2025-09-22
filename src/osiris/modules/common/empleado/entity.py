# src/osiris/modules/common/empleado/entity.py
from __future__ import annotations

from datetime import date
from uuid import UUID
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.types import Numeric, Date as SA_Date
from sqlmodel import Field

from src.osiris.domain.base_models import BaseTable, AuditMixin, SoftDeleteMixin


class Empleado(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_empleado"

    # FKs (sin relationships)
    persona_id: UUID = Field(foreign_key="tbl_persona.id", index=True, unique=True, nullable=False)

    # Campos de negocio solicitados
    salario: float = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    fecha_nacimiento: Optional[date] = Field(default=None, sa_column=Column(SA_Date, nullable=True))
    fecha_ingreso: date = Field(sa_column=Column(SA_Date, nullable=False))
    fecha_salida: Optional[date] = Field(default=None, sa_column=Column(SA_Date, nullable=True))
