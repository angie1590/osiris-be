# src/osiris/modules/inventario/tipo_producto/entity.py
from __future__ import annotations

from uuid import UUID
from sqlmodel import Field
from osiris.domain.base_models import BaseTable, AuditMixin, SoftDeleteMixin

class TipoProducto(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_tipo_producto"

    producto_id: UUID = Field(foreign_key="tbl_producto.id", index=True, nullable=False)
    atributo_id: UUID = Field(foreign_key="tbl_atributo.id", index=True, nullable=False)
    orden: int | None = Field(default=None)
    obligatorio: bool | None = Field(default=None)
    valor: str | None = Field(default=None, max_length=500)  # Valor aplicado al producto (stringificado según tipo_dato)
