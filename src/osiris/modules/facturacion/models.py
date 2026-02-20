from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from osiris.modules.common.empresa.entity import RegimenTributario
from osiris.modules.facturacion.entity import (
    EstadoCompra,
    FormaPagoSRI,
    SustentoTributarioSRI,
    TipoIdentificacionSRI,
    TipoImpuestoMVP,
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
    fecha_emision: date = Field(default_factory=date.today)
    bodega_id: UUID | None = None
    tipo_identificacion_comprador: TipoIdentificacionSRI
    identificacion_comprador: str = Field(..., min_length=3, max_length=20)
    forma_pago: FormaPagoSRI
    regimen_emisor: RegimenTributario = RegimenTributario.GENERAL
    usuario_auditoria: str
    detalles: list[VentaCompraDetalleCreate] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validar_iva_cero_para_negocio_popular(self):
        if self.regimen_emisor != RegimenTributario.RIMPE_NEGOCIO_POPULAR:
            return self

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


class VentaRegistroCreate(BaseModel):
    fecha_emision: date = Field(default_factory=date.today)
    bodega_id: UUID | None = None
    tipo_identificacion_comprador: TipoIdentificacionSRI
    identificacion_comprador: str = Field(..., min_length=3, max_length=20)
    forma_pago: FormaPagoSRI
    regimen_emisor: RegimenTributario = RegimenTributario.GENERAL
    usuario_auditoria: str
    detalles: list[VentaCompraDetalleRegistroCreate] = Field(..., min_length=1)


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
    fecha_emision: date
    tipo_identificacion_comprador: TipoIdentificacionSRI
    identificacion_comprador: str
    forma_pago: FormaPagoSRI
    regimen_emisor: RegimenTributario = RegimenTributario.GENERAL

    subtotal_sin_impuestos: Decimal
    subtotal_12: Decimal
    subtotal_15: Decimal
    subtotal_0: Decimal
    subtotal_no_objeto: Decimal
    monto_iva: Decimal
    monto_ice: Decimal
    valor_total: Decimal

    detalles: list[VentaDetalleRead]
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Alias de compatibilidad para referencias existentes en tests y módulos.
VentaDetalleImpuestoSnapshotRead = VentaDetalleImpuestoRead
