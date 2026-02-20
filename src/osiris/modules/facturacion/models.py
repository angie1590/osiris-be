from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, computed_field, model_validator

from osiris.modules.common.empresa.entity import RegimenTributario
from osiris.modules.facturacion.entity import (
    EstadoVenta,
    EstadoRetencionRecibida,
    EstadoSriDocumento,
    EstadoRetencion,
    EstadoCompra,
    FormaPagoSRI,
    SustentoTributarioSRI,
    TipoIdentificacionSRI,
    TipoEmisionVenta,
    TipoImpuestoMVP,
    TipoRetencionSRI,
)


CENT = Decimal("0.01")
IVA_12_CODES = {"2"}
IVA_15_CODES = {"4"}
IVA_0_CODES = {"0"}
IVA_NO_OBJETO_CODES = {"6"}


def q2(value: Decimal | int | str) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


class ImpuestoAplicadoInput(BaseModel):
    tipo_impuesto: TipoImpuestoMVP
    codigo_impuesto_sri: str = Field(..., min_length=1, max_length=10)
    codigo_porcentaje_sri: str = Field(..., min_length=1, max_length=10)
    tarifa: Decimal = Field(..., ge=Decimal("0"))

    @model_validator(mode="after")
    def validar_codigo_tipo(self):
        if self.tipo_impuesto == TipoImpuestoMVP.IVA and self.codigo_impuesto_sri != "2":
            raise ValueError("Para IVA, codigo_impuesto_sri debe ser '2'.")
        if self.tipo_impuesto == TipoImpuestoMVP.ICE and self.codigo_impuesto_sri != "3":
            raise ValueError("Para ICE, codigo_impuesto_sri debe ser '3'.")
        self.tarifa = q2(self.tarifa)
        return self


class VentaCompraDetalleCreate(BaseModel):
    producto_id: UUID
    descripcion: str = Field(..., min_length=1, max_length=255)
    cantidad: Decimal = Field(..., gt=Decimal("0"))
    precio_unitario: Decimal = Field(..., ge=Decimal("0"))
    descuento: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    es_actividad_excluida: bool = False
    impuestos: list[ImpuestoAplicadoInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def validar_impuestos_por_detalle(self):
        iva_count = sum(1 for i in self.impuestos if i.tipo_impuesto == TipoImpuestoMVP.IVA)
        ice_count = sum(1 for i in self.impuestos if i.tipo_impuesto == TipoImpuestoMVP.ICE)
        if iva_count > 1:
            raise ValueError("Un detalle no puede tener mas de un IVA.")
        if ice_count > 1:
            raise ValueError("Un detalle no puede tener mas de un ICE.")
        self.cantidad = Decimal(str(self.cantidad))
        self.precio_unitario = Decimal(str(self.precio_unitario))
        self.descuento = q2(self.descuento)
        return self

    @computed_field(return_type=Decimal)
    def subtotal_sin_impuesto(self) -> Decimal:
        bruto = Decimal(str(self.cantidad)) * Decimal(str(self.precio_unitario))
        return q2(bruto - self.descuento)

    def monto_ice_detalle(self) -> Decimal:
        total = Decimal("0.00")
        for ice in self.ice_impuestos():
            total += self.valor_impuesto(ice)
        return q2(total)

    def base_imponible_impuesto(self, impuesto: ImpuestoAplicadoInput) -> Decimal:
        base = self.subtotal_sin_impuesto
        if impuesto.tipo_impuesto == TipoImpuestoMVP.IVA:
            # Regla FE-EC: IVA se calcula sobre subtotal neto + ICE del detalle.
            base = q2(base + self.monto_ice_detalle())
        return q2(base)

    def valor_impuesto(self, impuesto: ImpuestoAplicadoInput) -> Decimal:
        base = self.base_imponible_impuesto(impuesto)
        return q2(base * impuesto.tarifa / Decimal("100"))

    def iva_impuesto(self) -> Optional[ImpuestoAplicadoInput]:
        for impuesto in self.impuestos:
            if impuesto.tipo_impuesto == TipoImpuestoMVP.IVA:
                return impuesto
        return None

    def ice_impuestos(self) -> list[ImpuestoAplicadoInput]:
        return [i for i in self.impuestos if i.tipo_impuesto == TipoImpuestoMVP.ICE]


class VentaCompraDetalleRegistroCreate(BaseModel):
    producto_id: UUID
    descripcion: str = Field(..., min_length=1, max_length=255)
    cantidad: Decimal = Field(..., gt=Decimal("0"))
    precio_unitario: Decimal = Field(..., ge=Decimal("0"))
    descuento: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    es_actividad_excluida: bool = False


class VentaCreate(BaseModel):
    cliente_id: UUID | None = None
    empresa_id: UUID | None = None
    punto_emision_id: UUID | None = None
    secuencial_formateado: str | None = Field(default=None, max_length=20)
    fecha_emision: date = Field(default_factory=date.today)
    bodega_id: UUID | None = None
    tipo_identificacion_comprador: TipoIdentificacionSRI
    identificacion_comprador: str = Field(..., min_length=3, max_length=20)
    forma_pago: FormaPagoSRI
    tipo_emision: TipoEmisionVenta | None = None
    regimen_emisor: RegimenTributario = RegimenTributario.GENERAL
    usuario_auditoria: str
    detalles: list[VentaCompraDetalleCreate] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validar_regimen_y_tipo_emision(self):
        if self.regimen_emisor != RegimenTributario.RIMPE_NEGOCIO_POPULAR:
            if self.tipo_emision == TipoEmisionVenta.NOTA_VENTA_FISICA:
                raise ValueError(
                    "NOTA_VENTA_FISICA solo está permitido para régimen RIMPE_NEGOCIO_POPULAR."
                )
            if self.tipo_emision is None:
                self.tipo_emision = TipoEmisionVenta.ELECTRONICA
            return self

        tiene_actividad_excluida = any(d.es_actividad_excluida for d in self.detalles)
        if tiene_actividad_excluida:
            if self.tipo_emision is None:
                self.tipo_emision = TipoEmisionVenta.ELECTRONICA
        else:
            # Regla SRI solicitada: RIMPE NP se emite como nota de venta física por defecto.
            self.tipo_emision = TipoEmisionVenta.NOTA_VENTA_FISICA

        for detalle in self.detalles:
            if detalle.es_actividad_excluida:
                continue
            iva = detalle.iva_impuesto()
            if iva and q2(iva.tarifa) > Decimal("0.00"):
                raise ValueError(
                    "Los Negocios Populares solo pueden facturar con tarifa 0% de IVA para sus actividades incluyentes"
                )
        return self

    @computed_field(return_type=Decimal)
    def subtotal_sin_impuestos(self) -> Decimal:
        return q2(sum((d.subtotal_sin_impuesto for d in self.detalles), Decimal("0.00")))

    @computed_field(return_type=Decimal)
    def subtotal_12(self) -> Decimal:
        total = Decimal("0.00")
        for detalle in self.detalles:
            iva = detalle.iva_impuesto()
            if iva and iva.codigo_porcentaje_sri in IVA_12_CODES:
                total += detalle.subtotal_sin_impuesto
        return q2(total)

    @computed_field(return_type=Decimal)
    def subtotal_15(self) -> Decimal:
        total = Decimal("0.00")
        for detalle in self.detalles:
            iva = detalle.iva_impuesto()
            if iva and iva.codigo_porcentaje_sri in IVA_15_CODES:
                total += detalle.subtotal_sin_impuesto
        return q2(total)

    @computed_field(return_type=Decimal)
    def subtotal_0(self) -> Decimal:
        total = Decimal("0.00")
        for detalle in self.detalles:
            iva = detalle.iva_impuesto()
            if iva and iva.codigo_porcentaje_sri in IVA_0_CODES:
                total += detalle.subtotal_sin_impuesto
        return q2(total)

    @computed_field(return_type=Decimal)
    def subtotal_no_objeto(self) -> Decimal:
        total = Decimal("0.00")
        for detalle in self.detalles:
            iva = detalle.iva_impuesto()
            if iva is None or iva.codigo_porcentaje_sri in IVA_NO_OBJETO_CODES:
                total += detalle.subtotal_sin_impuesto
        return q2(total)

    @computed_field(return_type=Decimal)
    def monto_iva(self) -> Decimal:
        total = Decimal("0.00")
        for detalle in self.detalles:
            iva = detalle.iva_impuesto()
            if iva:
                total += detalle.valor_impuesto(iva)
        return q2(total)

    @computed_field(return_type=Decimal)
    def monto_ice(self) -> Decimal:
        total = Decimal("0.00")
        for detalle in self.detalles:
            for ice in detalle.ice_impuestos():
                total += detalle.valor_impuesto(ice)
        return q2(total)

    @computed_field(return_type=Decimal)
    def valor_total(self) -> Decimal:
        return q2(self.subtotal_sin_impuestos + self.monto_iva + self.monto_ice)

    @computed_field(return_type=Decimal)
    def total(self) -> Decimal:
        return self.valor_total


class VentaRegistroCreate(BaseModel):
    cliente_id: UUID | None = None
    empresa_id: UUID | None = None
    punto_emision_id: UUID | None = None
    fecha_emision: date = Field(default_factory=date.today)
    bodega_id: UUID | None = None
    tipo_identificacion_comprador: TipoIdentificacionSRI
    identificacion_comprador: str = Field(..., min_length=3, max_length=20)
    forma_pago: FormaPagoSRI
    tipo_emision: TipoEmisionVenta | None = None
    regimen_emisor: RegimenTributario = RegimenTributario.GENERAL
    usuario_auditoria: str
    detalles: list[VentaCompraDetalleRegistroCreate] = Field(..., min_length=1)


class VentaUpdate(BaseModel):
    tipo_identificacion_comprador: TipoIdentificacionSRI | None = None
    identificacion_comprador: str | None = Field(default=None, min_length=3, max_length=20)
    forma_pago: FormaPagoSRI | None = None
    tipo_emision: TipoEmisionVenta | None = None
    usuario_auditoria: str


class VentaEmitRequest(BaseModel):
    usuario_auditoria: str


class CompraCreate(BaseModel):
    proveedor_id: UUID
    secuencial_factura: str = Field(..., pattern=r"^\d{3}-\d{3}-\d{9}$")
    autorizacion_sri: str = Field(..., pattern=r"^\d{37}$|^\d{49}$")
    fecha_emision: date = Field(default_factory=date.today)
    bodega_id: UUID | None = None
    sustento_tributario: SustentoTributarioSRI
    tipo_identificacion_proveedor: TipoIdentificacionSRI
    identificacion_proveedor: str = Field(..., min_length=3, max_length=20)
    forma_pago: FormaPagoSRI
    usuario_auditoria: str
    detalles: list[VentaCompraDetalleCreate] = Field(..., min_length=1)

    @computed_field(return_type=Decimal)
    def subtotal_sin_impuestos(self) -> Decimal:
        return q2(sum((d.subtotal_sin_impuesto for d in self.detalles), Decimal("0.00")))

    @computed_field(return_type=Decimal)
    def subtotal_12(self) -> Decimal:
        total = Decimal("0.00")
        for detalle in self.detalles:
            iva = detalle.iva_impuesto()
            if iva and iva.codigo_porcentaje_sri in IVA_12_CODES:
                total += detalle.subtotal_sin_impuesto
        return q2(total)

    @computed_field(return_type=Decimal)
    def subtotal_15(self) -> Decimal:
        total = Decimal("0.00")
        for detalle in self.detalles:
            iva = detalle.iva_impuesto()
            if iva and iva.codigo_porcentaje_sri in IVA_15_CODES:
                total += detalle.subtotal_sin_impuesto
        return q2(total)

    @computed_field(return_type=Decimal)
    def subtotal_0(self) -> Decimal:
        total = Decimal("0.00")
        for detalle in self.detalles:
            iva = detalle.iva_impuesto()
            if iva and iva.codigo_porcentaje_sri in IVA_0_CODES:
                total += detalle.subtotal_sin_impuesto
        return q2(total)

    @computed_field(return_type=Decimal)
    def subtotal_no_objeto(self) -> Decimal:
        total = Decimal("0.00")
        for detalle in self.detalles:
            iva = detalle.iva_impuesto()
            if iva is None or iva.codigo_porcentaje_sri in IVA_NO_OBJETO_CODES:
                total += detalle.subtotal_sin_impuesto
        return q2(total)

    @computed_field(return_type=Decimal)
    def monto_iva(self) -> Decimal:
        total = Decimal("0.00")
        for detalle in self.detalles:
            iva = detalle.iva_impuesto()
            if iva:
                total += detalle.valor_impuesto(iva)
        return q2(total)

    @computed_field(return_type=Decimal)
    def monto_ice(self) -> Decimal:
        total = Decimal("0.00")
        for detalle in self.detalles:
            for ice in detalle.ice_impuestos():
                total += detalle.valor_impuesto(ice)
        return q2(total)

    @computed_field(return_type=Decimal)
    def valor_total(self) -> Decimal:
        return q2(self.subtotal_sin_impuestos + self.monto_iva + self.monto_ice)


class CompraRegistroCreate(BaseModel):
    proveedor_id: UUID
    secuencial_factura: str = Field(..., pattern=r"^\d{3}-\d{3}-\d{9}$")
    autorizacion_sri: str = Field(..., pattern=r"^\d{37}$|^\d{49}$")
    fecha_emision: date = Field(default_factory=date.today)
    bodega_id: UUID | None = None
    sustento_tributario: SustentoTributarioSRI
    tipo_identificacion_proveedor: TipoIdentificacionSRI
    identificacion_proveedor: str = Field(..., min_length=3, max_length=20)
    forma_pago: FormaPagoSRI
    usuario_auditoria: str
    detalles: list[VentaCompraDetalleRegistroCreate] = Field(..., min_length=1)


class CompraUpdate(BaseModel):
    secuencial_factura: str | None = Field(default=None, pattern=r"^\d{3}-\d{3}-\d{9}$")
    autorizacion_sri: str | None = Field(default=None, pattern=r"^\d{37}$|^\d{49}$")
    fecha_emision: date | None = None
    sustento_tributario: SustentoTributarioSRI | None = None
    tipo_identificacion_proveedor: TipoIdentificacionSRI | None = None
    identificacion_proveedor: str | None = Field(default=None, min_length=3, max_length=20)
    forma_pago: FormaPagoSRI | None = None
    usuario_auditoria: str


class CompraAnularRequest(BaseModel):
    usuario_auditoria: str


class CompraRead(BaseModel):
    id: UUID
    proveedor_id: UUID
    secuencial_factura: str
    autorizacion_sri: str
    fecha_emision: date
    sustento_tributario: SustentoTributarioSRI
    tipo_identificacion_proveedor: TipoIdentificacionSRI
    identificacion_proveedor: str
    forma_pago: FormaPagoSRI
    subtotal_sin_impuestos: Decimal
    subtotal_12: Decimal
    subtotal_15: Decimal
    subtotal_0: Decimal
    subtotal_no_objeto: Decimal
    monto_iva: Decimal
    monto_ice: Decimal
    valor_total: Decimal
    estado: EstadoCompra
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PagoCxPCreate(BaseModel):
    monto: Decimal = Field(..., gt=Decimal("0"))
    fecha: date = Field(default_factory=date.today)
    forma_pago: FormaPagoSRI
    usuario_auditoria: str


class PagoCxPRead(BaseModel):
    id: UUID
    cuenta_por_pagar_id: UUID
    monto: Decimal
    fecha: date
    forma_pago: FormaPagoSRI

    model_config = ConfigDict(from_attributes=True)


class PlantillaRetencionDetalleInput(BaseModel):
    codigo_retencion_sri: str = Field(..., min_length=1, max_length=10)
    tipo: TipoRetencionSRI
    porcentaje: Decimal = Field(..., gt=Decimal("0"))

    @model_validator(mode="after")
    def normalizar_porcentaje(self):
        self.porcentaje = q2(self.porcentaje)
        return self


class GuardarPlantillaRetencionRequest(BaseModel):
    usuario_auditoria: str
    nombre: str = Field(default="Plantilla Retencion", min_length=1, max_length=150)
    es_global: bool = False
    detalles: list[PlantillaRetencionDetalleInput] = Field(..., min_length=1)


class PlantillaRetencionDetalleRead(BaseModel):
    id: UUID
    codigo_retencion_sri: str
    tipo: TipoRetencionSRI
    porcentaje: Decimal

    model_config = ConfigDict(from_attributes=True)


class PlantillaRetencionRead(BaseModel):
    id: UUID
    proveedor_id: UUID | None
    nombre: str
    es_global: bool
    detalles: list[PlantillaRetencionDetalleRead]

    model_config = ConfigDict(from_attributes=True)


class RetencionSugeridaDetalleRead(BaseModel):
    codigo_retencion_sri: str
    tipo: TipoRetencionSRI
    porcentaje: Decimal
    base_calculo: Decimal
    valor_retenido: Decimal


class RetencionSugeridaRead(BaseModel):
    compra_id: UUID
    plantilla_id: UUID
    proveedor_id: UUID | None
    detalles: list[RetencionSugeridaDetalleRead]
    total_retenido: Decimal


class RetencionDetalleCreate(BaseModel):
    codigo_retencion_sri: str = Field(..., min_length=1, max_length=10)
    tipo: TipoRetencionSRI
    porcentaje: Decimal = Field(..., gt=Decimal("0"))
    base_calculo: Decimal = Field(..., ge=Decimal("0"))

    @computed_field(return_type=Decimal)
    def valor_retenido(self) -> Decimal:
        return q2(q2(self.base_calculo) * q2(self.porcentaje) / Decimal("100"))


class RetencionCreate(BaseModel):
    fecha_emision: date = Field(default_factory=date.today)
    usuario_auditoria: str
    detalles: list[RetencionDetalleCreate] = Field(..., min_length=1)

    @computed_field(return_type=Decimal)
    def total_retenido(self) -> Decimal:
        return q2(sum((d.valor_retenido for d in self.detalles), Decimal("0.00")))


class RetencionEmitRequest(BaseModel):
    usuario_auditoria: str
    encolar: bool = False


class RetencionDetalleRead(BaseModel):
    id: UUID
    codigo_retencion_sri: str
    tipo: TipoRetencionSRI
    porcentaje: Decimal
    base_calculo: Decimal
    valor_retenido: Decimal

    model_config = ConfigDict(from_attributes=True)


class RetencionRead(BaseModel):
    id: UUID
    compra_id: UUID
    fecha_emision: date
    estado: EstadoRetencion
    estado_sri: EstadoSriDocumento
    sri_intentos: int = 0
    sri_ultimo_error: str | None = None
    total_retenido: Decimal
    detalles: list[RetencionDetalleRead]

    model_config = ConfigDict(from_attributes=True)


class RetencionRecibidaDetalleCreate(BaseModel):
    codigo_impuesto_sri: str = Field(..., pattern=r"^(1|2)$")
    porcentaje_aplicado: Decimal = Field(..., ge=Decimal("0"))
    base_imponible: Decimal = Field(..., ge=Decimal("0"))
    valor_retenido: Decimal = Field(..., ge=Decimal("0"))

    @model_validator(mode="after")
    def normalizar_montos(self):
        self.porcentaje_aplicado = q2(self.porcentaje_aplicado)
        self.base_imponible = q2(self.base_imponible)
        self.valor_retenido = q2(self.valor_retenido)
        return self


class RetencionRecibidaCreate(BaseModel):
    venta_id: UUID
    cliente_id: UUID
    numero_retencion: str = Field(..., pattern=r"^\d{3}-\d{3}-\d{9}$")
    clave_acceso_sri: str | None = Field(default=None, pattern=r"^\d{49}$")
    fecha_emision: date = Field(default_factory=date.today)
    estado: EstadoRetencionRecibida = EstadoRetencionRecibida.BORRADOR
    usuario_auditoria: str
    detalles: list[RetencionRecibidaDetalleCreate] = Field(..., min_length=1)

    @computed_field(return_type=Decimal)
    def total_retenido(self) -> Decimal:
        return q2(sum((d.valor_retenido for d in self.detalles), Decimal("0.00")))

    @model_validator(mode="after")
    def validar_reglas_tributarias_sri(self, info: ValidationInfo):
        # Esta validacion se ejecuta cuando el servicio inyecta el contexto de la venta.
        contexto = info.context or {}
        if not contexto:
            return self

        subtotal_general = q2(contexto.get("venta_subtotal_general", Decimal("0.00")))
        monto_iva_factura = q2(contexto.get("venta_monto_iva", Decimal("0.00")))

        for detalle in self.detalles:
            base = q2(detalle.base_imponible)
            if detalle.codigo_impuesto_sri == "1" and base > subtotal_general:
                raise ValueError(
                    "La base imponible de retencion en renta no puede superar el subtotal general de la venta."
                )

            if detalle.codigo_impuesto_sri == "2":
                if monto_iva_factura == Decimal("0.00"):
                    raise ValueError(
                        "Es ilegal registrar una retencion de IVA sobre una factura que no genera IVA"
                    )
                if base != monto_iva_factura:
                    raise ValueError(
                        "La base imponible de retencion IVA debe ser exactamente igual al monto IVA de la venta."
                    )

        return self


class RetencionRecibidaAnularRequest(BaseModel):
    motivo: str = Field(..., min_length=1, max_length=500)
    usuario_auditoria: str


class RetencionRecibidaDetalleRead(BaseModel):
    id: UUID
    codigo_impuesto_sri: str
    porcentaje_aplicado: Decimal
    base_imponible: Decimal
    valor_retenido: Decimal

    model_config = ConfigDict(from_attributes=True)


class RetencionRecibidaRead(BaseModel):
    id: UUID
    venta_id: UUID
    cliente_id: UUID
    numero_retencion: str
    clave_acceso_sri: str | None
    fecha_emision: date
    estado: EstadoRetencionRecibida
    total_retenido: Decimal
    detalles: list[RetencionRecibidaDetalleRead]

    model_config = ConfigDict(from_attributes=True)


class VentaDetalleImpuestoRead(BaseModel):
    tipo_impuesto: TipoImpuestoMVP
    codigo_impuesto_sri: str
    codigo_porcentaje_sri: str
    tarifa: Decimal
    base_imponible: Decimal
    valor_impuesto: Decimal


class VentaDetalleRead(BaseModel):
    producto_id: UUID
    descripcion: str
    cantidad: Decimal
    precio_unitario: Decimal
    descuento: Decimal
    subtotal_sin_impuesto: Decimal
    es_actividad_excluida: bool = False
    impuestos: list[VentaDetalleImpuestoRead]


class VentaRead(BaseModel):
    id: UUID
    cliente_id: UUID | None = None
    empresa_id: UUID | None = None
    punto_emision_id: UUID | None = None
    secuencial_formateado: str | None = None
    fecha_emision: date
    tipo_identificacion_comprador: TipoIdentificacionSRI
    identificacion_comprador: str
    forma_pago: FormaPagoSRI
    tipo_emision: TipoEmisionVenta = TipoEmisionVenta.ELECTRONICA
    regimen_emisor: RegimenTributario = RegimenTributario.GENERAL
    estado: EstadoVenta = EstadoVenta.EMITIDA
    estado_sri: EstadoSriDocumento = EstadoSriDocumento.PENDIENTE
    sri_intentos: int = 0
    sri_ultimo_error: str | None = None

    subtotal_sin_impuestos: Decimal
    subtotal_12: Decimal
    subtotal_15: Decimal
    subtotal_0: Decimal
    subtotal_no_objeto: Decimal
    monto_iva: Decimal
    monto_ice: Decimal
    valor_total: Decimal
    total: Decimal | None = None

    detalles: list[VentaDetalleRead]
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Alias de compatibilidad para referencias existentes en tests y módulos.
VentaDetalleImpuestoSnapshotRead = VentaDetalleImpuestoRead
