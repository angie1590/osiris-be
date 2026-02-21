from __future__ import annotations

from datetime import datetime
from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import Column, Numeric, Text, UniqueConstraint
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


class TipoRetencionSRI(str, Enum):
    RENTA = "RENTA"
    IVA = "IVA"


class EstadoRetencion(str, Enum):
    REGISTRADA = "REGISTRADA"
    BORRADOR = "BORRADOR"
    ENCOLADA = "ENCOLADA"
    EMITIDA = "EMITIDA"
    ANULADA = "ANULADA"


class EstadoVenta(str, Enum):
    BORRADOR = "BORRADOR"
    EMITIDA = "EMITIDA"
    ANULADA = "ANULADA"
    # Alias de compatibilidad con etapas previas.
    PENDIENTE = BORRADOR


class TipoEmisionVenta(str, Enum):
    ELECTRONICA = "ELECTRONICA"
    NOTA_VENTA_FISICA = "NOTA_VENTA_FISICA"


class EstadoCompra(str, Enum):
    BORRADOR = "BORRADOR"
    REGISTRADA = "REGISTRADA"
    ANULADA = "ANULADA"
    # Alias de compatibilidad con etapas previas.
    PENDIENTE = BORRADOR
    PAGADA = REGISTRADA


class EstadoCuentaPorPagar(str, Enum):
    PENDIENTE = "PENDIENTE"
    PARCIAL = "PARCIAL"
    PAGADA = "PAGADA"
    ANULADA = "ANULADA"


class EstadoCuentaPorCobrar(str, Enum):
    PENDIENTE = "PENDIENTE"
    PARCIAL = "PARCIAL"
    PAGADA = "PAGADA"
    ANULADA = "ANULADA"


class SustentoTributarioSRI(str, Enum):
    CREDITO_TRIBUTARIO_BIENES = "01"
    CREDITO_TRIBUTARIO_SERVICIOS = "02"
    SIN_CREDITO_TRIBUTARIO = "05"


class EstadoDocumentoElectronico(str, Enum):
    EN_COLA = "EN_COLA"
    FIRMADO = "FIRMADO"
    RECIBIDO = "RECIBIDO"
    ENVIADO = "ENVIADO"
    AUTORIZADO = "AUTORIZADO"
    RECHAZADO = "RECHAZADO"
    DEVUELTO = "DEVUELTO"


class TipoDocumentoElectronico(str, Enum):
    FACTURA = "FACTURA"
    RETENCION = "RETENCION"


class EstadoSriDocumento(str, Enum):
    PENDIENTE = "PENDIENTE"
    ENVIADO = "ENVIADO"
    REINTENTO = "REINTENTO"
    AUTORIZADO = "AUTORIZADO"
    RECHAZADO = "RECHAZADO"
    ERROR = "ERROR"


class EstadoColaSri(str, Enum):
    PENDIENTE = "PENDIENTE"
    PROCESANDO = "PROCESANDO"
    REINTENTO_PROGRAMADO = "REINTENTO_PROGRAMADO"
    COMPLETADO = "COMPLETADO"
    FALLIDO = "FALLIDO"


class EstadoRetencionRecibida(str, Enum):
    BORRADOR = "BORRADOR"
    APLICADA = "APLICADA"
    ANULADA = "ANULADA"


class Venta(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_venta"

    cliente_id: UUID | None = Field(default=None, nullable=True, index=True)
    empresa_id: UUID | None = Field(default=None, foreign_key="tbl_empresa.id", nullable=True, index=True)
    punto_emision_id: UUID | None = Field(
        default=None,
        foreign_key="tbl_punto_emision.id",
        nullable=True,
        index=True,
    )
    secuencial_formateado: str | None = Field(default=None, max_length=20, nullable=True, index=True)
    fecha_emision: date = Field(default_factory=date.today, nullable=False)
    tipo_identificacion_comprador: TipoIdentificacionSRI = Field(nullable=False, max_length=20)
    identificacion_comprador: str = Field(nullable=False, max_length=20, index=True)
    forma_pago: FormaPagoSRI = Field(nullable=False, max_length=20)
    regimen_emisor: RegimenTributario = Field(default=RegimenTributario.GENERAL, nullable=False)
    tipo_emision: TipoEmisionVenta = Field(default=TipoEmisionVenta.ELECTRONICA, nullable=False, max_length=25)

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
    estado_sri: EstadoSriDocumento = Field(
        default=EstadoSriDocumento.PENDIENTE,
        nullable=False,
        max_length=20,
    )
    sri_intentos: int = Field(default=0, nullable=False)
    sri_ultimo_error: str | None = Field(default=None, max_length=1000)


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

    tipo_documento: TipoDocumentoElectronico = Field(
        default=TipoDocumentoElectronico.FACTURA,
        nullable=False,
        max_length=20,
        index=True,
    )
    referencia_id: UUID | None = Field(default=None, nullable=True, index=True)
    venta_id: UUID | None = Field(default=None, foreign_key="tbl_venta.id", nullable=True, index=True)
    clave_acceso: str | None = Field(default=None, max_length=49, nullable=True, index=True)
    estado_sri: EstadoDocumentoElectronico = Field(
        default=EstadoDocumentoElectronico.EN_COLA,
        nullable=False,
        max_length=20,
    )
    # Campo legado para compatibilidad con código/tests previos.
    estado: EstadoDocumentoElectronico = Field(
        default=EstadoDocumentoElectronico.EN_COLA,
        nullable=False,
        max_length=20,
    )
    mensajes_sri: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    xml_autorizado: str | None = Field(default=None, sa_column=Column(Text, nullable=True))


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

    proveedor_id: UUID = Field(nullable=False, index=True)
    secuencial_factura: str = Field(nullable=False, max_length=20, index=True)
    autorizacion_sri: str = Field(nullable=False, max_length=49, index=True)
    fecha_emision: date = Field(default_factory=date.today, nullable=False)
    sustento_tributario: SustentoTributarioSRI = Field(nullable=False, max_length=5)
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
    estado: EstadoCompra = Field(default=EstadoCompra.BORRADOR, nullable=False, max_length=20)


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


class CuentaPorPagar(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_cuenta_por_pagar"

    compra_id: UUID = Field(foreign_key="tbl_compra.id", nullable=False, index=True, unique=True)
    valor_total_factura: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    valor_retenido: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00")))
    pagos_acumulados: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00")))
    saldo_pendiente: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    estado: EstadoCuentaPorPagar = Field(default=EstadoCuentaPorPagar.PENDIENTE, nullable=False, max_length=20)


class PagoCxP(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_pago_cxp"

    cuenta_por_pagar_id: UUID = Field(foreign_key="tbl_cuenta_por_pagar.id", nullable=False, index=True)
    monto: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    fecha: date = Field(default_factory=date.today, nullable=False, index=True)
    forma_pago: FormaPagoSRI = Field(nullable=False, max_length=20)


class CuentaPorCobrar(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_cuenta_por_cobrar"

    venta_id: UUID = Field(foreign_key="tbl_venta.id", nullable=False, index=True, unique=True)
    valor_total_factura: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    valor_retenido: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00")))
    pagos_acumulados: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False, default=Decimal("0.00")))
    saldo_pendiente: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    estado: EstadoCuentaPorCobrar = Field(default=EstadoCuentaPorCobrar.PENDIENTE, nullable=False, max_length=20)


class PagoCxC(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_pago_cxc"

    cuenta_por_cobrar_id: UUID = Field(foreign_key="tbl_cuenta_por_cobrar.id", nullable=False, index=True)
    monto: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    fecha: date = Field(default_factory=date.today, nullable=False, index=True)
    forma_pago_sri: FormaPagoSRI = Field(nullable=False, max_length=20)


class PlantillaRetencion(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_plantilla_retencion"

    proveedor_id: UUID | None = Field(default=None, nullable=True, index=True)
    nombre: str = Field(nullable=False, max_length=150, default="Plantilla Retencion")
    es_global: bool = Field(default=False, nullable=False, index=True)


class PlantillaRetencionDetalle(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_plantilla_retencion_detalle"

    plantilla_retencion_id: UUID = Field(
        foreign_key="tbl_plantilla_retencion.id",
        nullable=False,
        index=True,
    )
    codigo_retencion_sri: str = Field(nullable=False, min_length=1, max_length=10)
    tipo: TipoRetencionSRI = Field(nullable=False, max_length=20)
    porcentaje: Decimal = Field(sa_column=Column(Numeric(7, 4), nullable=False))


class Retencion(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_retencion"

    compra_id: UUID = Field(foreign_key="tbl_compra.id", nullable=False, index=True, unique=True)
    fecha_emision: date = Field(default_factory=date.today, nullable=False, index=True)
    estado: EstadoRetencion = Field(default=EstadoRetencion.BORRADOR, nullable=False, max_length=20)
    estado_sri: EstadoSriDocumento = Field(
        default=EstadoSriDocumento.PENDIENTE,
        nullable=False,
        max_length=20,
    )
    sri_intentos: int = Field(default=0, nullable=False)
    sri_ultimo_error: str | None = Field(default=None, max_length=1000)
    total_retenido: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))


class RetencionDetalle(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_retencion_detalle"

    retencion_id: UUID = Field(foreign_key="tbl_retencion.id", nullable=False, index=True)
    codigo_retencion_sri: str = Field(nullable=False, min_length=1, max_length=10)
    tipo: TipoRetencionSRI = Field(nullable=False, max_length=20)
    porcentaje: Decimal = Field(sa_column=Column(Numeric(7, 4), nullable=False))
    base_calculo: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    valor_retenido: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))


class RetencionEstadoHistorial(BaseTable, table=True):
    __tablename__ = "tbl_retencion_estado_historial"

    entidad_id: UUID = Field(foreign_key="tbl_retencion.id", nullable=False, index=True)
    estado_anterior: str = Field(nullable=False, max_length=30)
    estado_nuevo: str = Field(nullable=False, max_length=30)
    motivo_cambio: str = Field(sa_column=Column(Text, nullable=False))
    usuario_id: str | None = Field(default=None, max_length=255, index=True)
    fecha: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)


class DocumentoSriCola(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_documento_sri_cola"

    entidad_id: UUID = Field(nullable=False, index=True)
    tipo_documento: str = Field(nullable=False, max_length=30, index=True)
    estado: EstadoColaSri = Field(default=EstadoColaSri.PENDIENTE, nullable=False, max_length=30)
    intentos_realizados: int = Field(default=0, nullable=False)
    max_intentos: int = Field(default=3, nullable=False)
    proximo_intento_en: datetime | None = Field(default=None, nullable=True, index=True)
    ultimo_error: str | None = Field(default=None, max_length=1000)
    payload_json: str = Field(sa_column=Column(Text, nullable=False))


class RetencionRecibida(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_retencion_recibida"
    __table_args__ = (
        UniqueConstraint(
            "cliente_id",
            "numero_retencion",
            name="uq_retencion_recibida_cliente_numero",
        ),
    )

    venta_id: UUID = Field(foreign_key="tbl_venta.id", nullable=False, index=True)
    cliente_id: UUID = Field(nullable=False, index=True)
    numero_retencion: str = Field(nullable=False, max_length=20)
    clave_acceso_sri: str | None = Field(default=None, max_length=49, nullable=True, index=True)
    fecha_emision: date = Field(default_factory=date.today, nullable=False, index=True)
    estado: EstadoRetencionRecibida = Field(
        default=EstadoRetencionRecibida.BORRADOR,
        nullable=False,
        max_length=20,
    )
    total_retenido: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))


class RetencionRecibidaDetalle(BaseTable, AuditMixin, SoftDeleteMixin, table=True):
    __tablename__ = "tbl_retencion_recibida_detalle"

    retencion_recibida_id: UUID = Field(
        foreign_key="tbl_retencion_recibida.id",
        nullable=False,
        index=True,
    )
    codigo_impuesto_sri: str = Field(nullable=False, max_length=5)
    porcentaje_aplicado: Decimal = Field(sa_column=Column(Numeric(7, 4), nullable=False))
    base_imponible: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    valor_retenido: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))


class RetencionRecibidaEstadoHistorial(BaseTable, table=True):
    __tablename__ = "tbl_retencion_recibida_estado_historial"

    entidad_id: UUID = Field(foreign_key="tbl_retencion_recibida.id", nullable=False, index=True)
    estado_anterior: str = Field(nullable=False, max_length=30)
    estado_nuevo: str = Field(nullable=False, max_length=30)
    motivo_cambio: str = Field(sa_column=Column(Text, nullable=False))
    usuario_id: str | None = Field(default=None, max_length=255, index=True)
    fecha: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)


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
