from __future__ import annotations
from typing import Optional
from sqlmodel import Field

from osiris.domain.base_models import BaseTable, AuditMixin, SoftDeleteMixin


class Empresa(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_empresa"

    razon_social: str = Field(index=True, nullable=False, max_length=255)
    nombre_comercial: Optional[str] = Field(default=None, max_length=255)

    # RUC ecuatoriano (13)
    ruc: str = Field(index=True, nullable=False, max_length=13)

    direccion_matriz: str = Field(nullable=False, max_length=255)
    telefono: Optional[str] = Field(default=None, max_length=15)
    logo: Optional[str] = Field(default=None, max_length=500)

    # Algunas implantaciones manejan esto a nivel Empresa; si no aplica, déjalo tal cual
    codigo_establecimiento: Optional[str] = Field(default=None, max_length=3)
    obligado_contabilidad: bool = Field(default=False)

    # FK al catálogo (PK = 'codigo')
    tipo_contribuyente_id: str = Field(
        foreign_key="aux_tipo_contribuyente.codigo",
        nullable=False,
        max_length=2,
    )
