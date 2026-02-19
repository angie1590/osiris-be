from __future__ import annotations

from datetime import datetime
from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import Column, Numeric, Text
from sqlmodel import Field

from osiris.domain.base_models import AuditMixin, BaseTable, SoftDeleteMixin
from osiris.modules.common.empresa.entity import RegimenTributario


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


class EstadoVenta(str, Enum):
    PENDIENTE = "PENDIENTE"
    EMITIDA = "EMITIDA"
    ANULADA = "ANULADA"


class EstadoCompra(str, Enum):
    PENDIENTE = "PENDIENTE"
    PAGADA = "PAGADA"
    ANULADA = "ANULADA"


class EstadoDocumentoElectronico(str, Enum):
    ENVIADO = "ENVIADO"
    AUTORIZADO = "AUTORIZADO"
    RECHAZADO = "RECHAZADO"


class Venta(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_venta"

    fecha_emision: date = Field(default_factory=date.today, nullable=False)
    tipo_identificacion_comprador: TipoIdentificacionSRI = Field(nullable=False, max_length=20)
    identificacion_comprador: str = Field(nullable=False, max_length=20, index=True)
    forma_pago: FormaPagoSRI = Field(nullable=False, max_length=20)
    regimen_emisor: RegimenTributario = Field(default=RegimenTributario.GENERAL, nullable=False)

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
    estado: EstadoVenta = Field(default=EstadoVenta.EMITIDA, nullable=False, max_length=20)


class VentaDetalle(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_venta_detalle"

    venta_id: UUID = Field(foreign_key="tbl_venta.id", nullable=False, index=True)
    producto_id: UUID = Field(foreign_key="tbl_producto.id", nullable=False, index=True)

    descripcion: str = Field(nullable=False, max_length=255)
    cantidad: Decimal = Field(sa_column=Column(Numeric(12, 4), nullable=False))
    precio_unitario: Decimal = Field(sa_column=Column(Numeric(12, 4), nullable=False))
    descuento: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00")))
    subtotal_sin_impuesto: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    es_actividad_excluida: bool = Field(default=False, nullable=False)


class VentaDetalleImpuesto(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_venta_detalle_impuesto"

    venta_detalle_id: UUID = Field(foreign_key="tbl_venta_detalle.id", nullable=False, index=True)

    tipo_impuesto: TipoImpuestoMVP = Field(nullable=False, max_length=10)
    codigo_impuesto_sri: str = Field(nullable=False, max_length=10)
    codigo_porcentaje_sri: str = Field(nullable=False, max_length=10)
    tarifa: Decimal = Field(sa_column=Column(Numeric(7, 4), nullable=False))
    base_imponible: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    valor_impuesto: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))


# Alias de compatibilidad para referencias existentes.
VentaDetalleImpuestoSnapshot = VentaDetalleImpuesto


class DocumentoElectronico(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_documento_electronico"

    venta_id: UUID = Field(foreign_key="tbl_venta.id", nullable=False, index=True)
    clave_acceso: str = Field(nullable=False, max_length=49, index=True)
    estado: EstadoDocumentoElectronico = Field(
        default=EstadoDocumentoElectronico.ENVIADO,
        nullable=False,
        max_length=20,
    )


class VentaEstadoHistorial(BaseTable, table=True):
    __tablename__ = "tbl_venta_estado_historial"

    entidad_id: UUID = Field(foreign_key="tbl_venta.id", nullable=False, index=True)
    estado_anterior: str = Field(nullable=False, max_length=30)
    estado_nuevo: str = Field(nullable=False, max_length=30)
    motivo_cambio: str = Field(sa_column=Column(Text, nullable=False))
    usuario_id: str | None = Field(default=None, max_length=255, index=True)
    fecha: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)


class DocumentoElectronicoHistorial(BaseTable, table=True):
    __tablename__ = "tbl_documento_electronico_historial"

    entidad_id: UUID = Field(foreign_key="tbl_documento_electronico.id", nullable=False, index=True)
    estado_anterior: str = Field(nullable=False, max_length=30)
    estado_nuevo: str = Field(nullable=False, max_length=30)
    motivo_cambio: str = Field(sa_column=Column(Text, nullable=False))
    usuario_id: str | None = Field(default=None, max_length=255, index=True)
    fecha: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)


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
    estado: EstadoCompra = Field(default=EstadoCompra.PENDIENTE, nullable=False, max_length=20)


class CompraDetalle(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_compra_detalle"

    compra_id: UUID = Field(foreign_key="tbl_compra.id", nullable=False, index=True)
    producto_id: UUID = Field(foreign_key="tbl_producto.id", nullable=False, index=True)

    descripcion: str = Field(nullable=False, max_length=255)
    cantidad: Decimal = Field(sa_column=Column(Numeric(12, 4), nullable=False))
    precio_unitario: Decimal = Field(sa_column=Column(Numeric(12, 4), nullable=False))
    descuento: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00")))
    subtotal_sin_impuesto: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))


class CompraDetalleImpuesto(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_compra_detalle_impuesto"

    compra_detalle_id: UUID = Field(foreign_key="tbl_compra_detalle.id", nullable=False, index=True)

    tipo_impuesto: TipoImpuestoMVP = Field(nullable=False, max_length=10)
    codigo_impuesto_sri: str = Field(nullable=False, max_length=10)
    codigo_porcentaje_sri: str = Field(nullable=False, max_length=10)
    tarifa: Decimal = Field(sa_column=Column(Numeric(7, 4), nullable=False))
    base_imponible: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    valor_impuesto: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))


# Alias de compatibilidad para referencias existentes.
CompraDetalleImpuestoSnapshot = CompraDetalleImpuesto


class CompraEstadoHistorial(BaseTable, table=True):
    __tablename__ = "tbl_compra_estado_historial"

    entidad_id: UUID = Field(foreign_key="tbl_compra.id", nullable=False, index=True)
    estado_anterior: str = Field(nullable=False, max_length=30)
    estado_nuevo: str = Field(nullable=False, max_length=30)
    motivo_cambio: str = Field(sa_column=Column(Text, nullable=False))
    usuario_id: str | None = Field(default=None, max_length=255, index=True)
    fecha: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
