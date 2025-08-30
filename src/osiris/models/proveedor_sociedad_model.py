from pydantic import BaseModel, Field, EmailStr, model_validator
from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict

from src.osiris.utils.validacion_identificacion import ValidacionCedulaRucService


class ProveedorSociedadBase(BaseModel):
    ruc: str
    razon_social: str
    nombre_comercial: Optional[str] = None
    direccion: str
    telefono: Optional[str]
    email: EmailStr
    tipo_contribuyente_id: str = Field(min_length=2, max_length=2)
    identificacion_contacto: str

    @model_validator(mode="after")
    def validar_ruc(cls, values):
        ruc = values.ruc
        if not ValidacionCedulaRucService.es_identificacion_valida(ruc):
            raise ValueError("El RUC ingresado no es válido.")
        return values


class ProveedorSociedadCrear(ProveedorSociedadBase):
    usuario_auditoria: str


class ProveedorSociedadActualizar(BaseModel):
    razon_social: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    tipo_contribuyente_id: Optional[str] = None
    persona_contacto_id: Optional[UUID] = None
    activo: Optional[bool] = None
    usuario_auditoria: str

    @model_validator(mode="after")
    def validar_ruc_en_actualizacion(cls, values):
        return values

class ProveedorSociedadInput(BaseModel):
    ruc: str
    razon_social: str
    nombre_comercial: Optional[str] = None
    direccion: str
    telefono: Optional[str]
    email: EmailStr
    tipo_contribuyente_id: str = Field(min_length=2, max_length=2)
    identificacion_contacto: str
    usuario_auditoria: str

class ProveedorSociedadRespuesta(BaseModel):
    id: UUID
    ruc: str
    razon_social: str
    nombre_comercial: Optional[str] = None
    direccion: str
    telefono: Optional[str]
    email: EmailStr
    tipo_contribuyente_id: str
    persona_contacto_id: UUID
    activo: bool
    fecha_creacion: datetime
    fecha_modificacion: datetime
    usuario_auditoria: Optional[str]

    model_config = ConfigDict(from_attributes=True)
