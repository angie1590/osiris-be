# src/osiris/modules/common/empresa/models.py
from __future__ import annotations
from typing import Optional, Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator
from src.osiris.utils.validacion_identificacion import ValidacionCedulaRucService


# Atajos de tipos con restricciones
RazonSocial = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r'^[A-Za-zÁÉÍÓÚÑáéíóúñ\s]+$')]
NombreComercial = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r'^[A-Za-zÁÉÍÓÚÑáéíóúñ0-9\s\.\,\-]+$')]
RUC = Annotated[str, StringConstraints(min_length=13, max_length=13, pattern=r'^\d{13}$')]
Telefono = Annotated[str, StringConstraints(pattern=r'^\d{7,10}$')]
CodigoEst = Annotated[str, StringConstraints(min_length=3, max_length=3, pattern=r'^\d{3}$')]
TipoContribuyenteID = Annotated[str, StringConstraints(min_length=2, max_length=2)]


class EmpresaBase(BaseModel):
    razon_social: RazonSocial
    nombre_comercial: Optional[NombreComercial] = None
    ruc: RUC
    direccion_matriz: str
    telefono: Optional[Telefono] = None
    codigo_establecimiento: Optional[CodigoEst] = None
    obligado_contabilidad: bool = False
    tipo_contribuyente_id: TipoContribuyenteID
    usuario_auditoria: str

    @field_validator("ruc")
    @classmethod
    def _validar_ruc(cls, v: str) -> str:
        if not ValidacionCedulaRucService.es_identificacion_valida(v):
            raise ValueError("El RUC ingresado no es válido.")
        return v


class EmpresaCreate(EmpresaBase):
    """POST/PUT (reemplazo total)."""


class EmpresaUpdate(BaseModel):
    razon_social: Optional[RazonSocial] = None
    nombre_comercial: Optional[NombreComercial] = None
    ruc: Optional[RUC] = None
    direccion_matriz: Optional[str] = None
    telefono: Optional[Telefono] = None
    codigo_establecimiento: Optional[CodigoEst] = None
    obligado_contabilidad: Optional[bool] = None
    tipo_contribuyente_id: Optional[TipoContribuyenteID] = None
    usuario_auditoria: Optional[str] = None

    @field_validator("ruc")
    @classmethod
    def _validar_ruc_opt(cls, v: str) -> str:
        if v is not None and not ValidacionCedulaRucService.es_identificacion_valida(v):
            raise ValueError("El RUC ingresado no es válido.")
        return v


class EmpresaRead(EmpresaBase):
    id: UUID
    activo: bool
    model_config = ConfigDict(from_attributes=True)
