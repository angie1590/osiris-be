from __future__ import annotations

from typing import Optional
from datetime import date
from decimal import Decimal
from uuid import UUID
from pydantic import field_validator, model_validator

from osiris.domain.base_models import BaseOSModel
from osiris.modules.aux.impuesto_catalogo.entity import (
    TipoImpuesto,
    ClasificacionIVA,
    ModoCalculoICE,
    UnidadBase,
    AplicaA,
)


class ImpuestoCatalogoCreate(BaseOSModel):
    tipo_impuesto: TipoImpuesto
    codigo_sri: str
    descripcion: str
    vigente_desde: date
    vigente_hasta: Optional[date] = None
    aplica_a: AplicaA

    # Campos IVA
    porcentaje_iva: Optional[Decimal] = None
    clasificacion_iva: Optional[ClasificacionIVA] = None

    # Campos ICE
    tarifa_ad_valorem: Optional[Decimal] = None
    tarifa_especifica: Optional[Decimal] = None
    modo_calculo_ice: Optional[ModoCalculoICE] = None
    unidad_base: Optional[UnidadBase] = None

    usuario_auditoria: Optional[str] = None

    @model_validator(mode="after")
    def validate_impuesto_fields(self):
        """Valida que los campos obligatorios estén presentes según el tipo de impuesto."""
        if self.tipo_impuesto == TipoImpuesto.IVA:
            if self.porcentaje_iva is None:
                raise ValueError("porcentaje_iva es obligatorio para IVA")
            if self.clasificacion_iva is None:
                raise ValueError("clasificacion_iva es obligatorio para IVA")

        elif self.tipo_impuesto == TipoImpuesto.ICE:
            if self.tarifa_ad_valorem is None and self.tarifa_especifica is None:
                raise ValueError("Al menos una tarifa (ad_valorem o especifica) es obligatoria para ICE")
            if self.modo_calculo_ice is None:
                raise ValueError("modo_calculo_ice es obligatorio para ICE")
            if self.unidad_base is None:
                raise ValueError("unidad_base es obligatorio para ICE")

        # Validar vigencia
        if self.vigente_hasta is not None and self.vigente_hasta < self.vigente_desde:
            raise ValueError("vigente_hasta debe ser mayor o igual a vigente_desde")

        return self


class ImpuestoCatalogoUpdate(BaseOSModel):
    descripcion: Optional[str] = None
    vigente_hasta: Optional[date] = None
    aplica_a: Optional[AplicaA] = None

    # Campos IVA
    porcentaje_iva: Optional[Decimal] = None
    clasificacion_iva: Optional[ClasificacionIVA] = None

    # Campos ICE
    tarifa_ad_valorem: Optional[Decimal] = None
    tarifa_especifica: Optional[Decimal] = None
    modo_calculo_ice: Optional[ModoCalculoICE] = None
    unidad_base: Optional[UnidadBase] = None

    usuario_auditoria: Optional[str] = None


class ImpuestoCatalogoRead(BaseOSModel):
    id: UUID
    tipo_impuesto: TipoImpuesto
    codigo_sri: str
    descripcion: str
    vigente_desde: date
    vigente_hasta: Optional[date] = None
    aplica_a: AplicaA
    activo: bool

    # Campos IVA
    porcentaje_iva: Optional[Decimal] = None
    clasificacion_iva: Optional[ClasificacionIVA] = None

    # Campos ICE
    tarifa_ad_valorem: Optional[Decimal] = None
    tarifa_especifica: Optional[Decimal] = None
    modo_calculo_ice: Optional[ModoCalculoICE] = None
    unidad_base: Optional[UnidadBase] = None
