from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import Column, Numeric
from sqlmodel import Field

from osiris.domain.base_models import AuditMixin, BaseTable, SoftDeleteMixin


class TipoIdentificacionSRI(str, Enum):
    RUC = "RUC"
    CEDULA = "CEDULA"
    PASAPORTE = "PASAPORTE"


class FormaPagoSRI(str, Enum):
    EFECTIVO = "EFECTIVO"
    TARJETA = "TARJETA"
    TRANSFERENCIA = "TRANSFERENCIA"


class TipoImpuestoMVP(str, Enum):
    IVA = "IVA"
    ICE = "ICE"


class Venta(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_venta"

    fecha_emision: date = Field(default_factory=date.today, nullable=False)
    tipo_identificacion_comprador: TipoIdentificacionSRI = Field(nullable=False, max_length=20)
    identificacion_comprador: str = Field(nullable=False, max_length=20, index=True)
    forma_pago: FormaPagoSRI = Field(nullable=False, max_length=20)

    subtotal_sin_impuestos: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    subtotal_12: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00")))
    subtotal_15: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00")))
    subtotal_0: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00")))
    subtotal_no_objeto: Decimal = Field(
        sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    )
    monto_iva: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00")))
    monto_ice: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00")))
    valor_total: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))


class VentaDetalle(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_venta_detalle"

    venta_id: UUID = Field(foreign_key="tbl_venta.id", nullable=False, index=True)
    producto_id: UUID = Field(foreign_key="tbl_producto.id", nullable=False, index=True)

    descripcion: str = Field(nullable=False, max_length=255)
    cantidad: Decimal = Field(sa_column=Column(Numeric(12, 4), nullable=False))
    precio_unitario: Decimal = Field(sa_column=Column(Numeric(12, 4), nullable=False))
    descuento: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00")))
    subtotal_sin_impuesto: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))


class VentaDetalleImpuestoSnapshot(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_venta_detalle_impuesto"

    venta_detalle_id: UUID = Field(foreign_key="tbl_venta_detalle.id", nullable=False, index=True)

    tipo_impuesto: TipoImpuestoMVP = Field(nullable=False, max_length=10)
    codigo_impuesto_sri: str = Field(nullable=False, max_length=10)
    codigo_porcentaje_sri: str = Field(nullable=False, max_length=10)
    tarifa: Decimal = Field(sa_column=Column(Numeric(7, 4), nullable=False))
    base_imponible: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    valor_impuesto: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))


class Compra(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_compra"

    fecha_emision: date = Field(default_factory=date.today, nullable=False)
    tipo_identificacion_proveedor: TipoIdentificacionSRI = Field(nullable=False, max_length=20)
    identificacion_proveedor: str = Field(nullable=False, max_length=20, index=True)
    forma_pago: FormaPagoSRI = Field(nullable=False, max_length=20)

    subtotal_sin_impuestos: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    subtotal_12: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00")))
    subtotal_15: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00")))
    subtotal_0: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00")))
    subtotal_no_objeto: Decimal = Field(
        sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    )
    monto_iva: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00")))
    monto_ice: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00")))
    valor_total: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))


class CompraDetalle(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_compra_detalle"

    compra_id: UUID = Field(foreign_key="tbl_compra.id", nullable=False, index=True)
    producto_id: UUID = Field(foreign_key="tbl_producto.id", nullable=False, index=True)

    descripcion: str = Field(nullable=False, max_length=255)
    cantidad: Decimal = Field(sa_column=Column(Numeric(12, 4), nullable=False))
    precio_unitario: Decimal = Field(sa_column=Column(Numeric(12, 4), nullable=False))
    descuento: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00")))
    subtotal_sin_impuesto: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))


class CompraDetalleImpuestoSnapshot(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_compra_detalle_impuesto"

    compra_detalle_id: UUID = Field(foreign_key="tbl_compra_detalle.id", nullable=False, index=True)

    tipo_impuesto: TipoImpuestoMVP = Field(nullable=False, max_length=10)
    codigo_impuesto_sri: str = Field(nullable=False, max_length=10)
    codigo_porcentaje_sri: str = Field(nullable=False, max_length=10)
    tarifa: Decimal = Field(sa_column=Column(Numeric(7, 4), nullable=False))
    base_imponible: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    valor_impuesto: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
