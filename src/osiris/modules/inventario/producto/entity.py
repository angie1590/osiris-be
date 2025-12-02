# src/osiris/modules/inventario/producto/entity.py
from __future__ import annotations

from enum import Enum
from uuid import UUID
from decimal import Decimal
from sqlmodel import Field, Relationship, Column, Numeric
from osiris.domain.base_models import BaseTable, AuditMixin, SoftDeleteMixin


class TipoProducto(str, Enum):
    BIEN = "BIEN"
    SERVICIO = "SERVICIO"


class Producto(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_producto"

    nombre: str = Field(index=True, nullable=False, unique=True, max_length=255)
    tipo: TipoProducto = Field(nullable=False, default=TipoProducto.BIEN)
    pvp: Decimal = Field(
        sa_column=Column(Numeric(10, 2), nullable=False),
        default=Decimal("0.00")
    )
    # Nueva columna: cantidad en inventario. Se inicializa a 0 y no la ingresa el usuario en la creación
    cantidad: int = Field(default=0, nullable=False)
    casa_comercial_id: UUID | None = Field(default=None, foreign_key="tbl_casa_comercial.id")

    # Relaciones M:N se materializan con tablas puente externas (no se declaran aquí para reducir acoplamiento)

# Puente: Producto-Categoría (solo nodos hoja)
class ProductoCategoria(BaseTable, table=True):
    __tablename__ = "tbl_producto_categoria"

    producto_id: UUID = Field(foreign_key="tbl_producto.id", index=True, nullable=False)
    categoria_id: UUID = Field(foreign_key="tbl_categoria.id", index=True, nullable=False)

# Puente: Producto-Proveedor Persona
class ProductoProveedorPersona(BaseTable, table=True):
    __tablename__ = "tbl_producto_proveedor_persona"

    producto_id: UUID = Field(foreign_key="tbl_producto.id", index=True, nullable=False)
    proveedor_persona_id: UUID = Field(foreign_key="tbl_proveedor_persona.id", index=True, nullable=False)

# Puente: Producto-Proveedor Sociedad
class ProductoProveedorSociedad(BaseTable, table=True):
    __tablename__ = "tbl_producto_proveedor_sociedad"

    producto_id: UUID = Field(foreign_key="tbl_producto.id", index=True, nullable=False)
    proveedor_sociedad_id: UUID = Field(foreign_key="tbl_proveedor_sociedad.id", index=True, nullable=False)


# Puente: Producto-Impuesto
class ProductoImpuesto(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_producto_impuesto"

    producto_id: UUID = Field(foreign_key="tbl_producto.id", index=True, nullable=False)
    impuesto_catalogo_id: UUID = Field(foreign_key="aux_impuesto_catalogo.id", index=True, nullable=False)

    # Restricción única: un impuesto específico solo se puede asignar una vez a un producto
    # Se implementará en la migración como UNIQUE(producto_id, impuesto_catalogo_id)
