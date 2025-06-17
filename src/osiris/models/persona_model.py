from enum import Enum
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from uuid import UUID
from typing import Optional
from datetime import datetime

from src.osiris.utils.validacion_identificacion import ValidacionCedulaRucService


class TipoIdentificacion(str, Enum):
    CEDULA = "CEDULA"
    RUC = "RUC"
    PASAPORTE = "PASAPORTE"


class PersonaBase(BaseModel):
    identificacion: str
    tipo_identificacion: TipoIdentificacion
    nombre: str
    apellido: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    ciudad: Optional[str] = None
    email: Optional[EmailStr] = None


class PersonaCrear(PersonaBase):
    usuario_auditoria: str

    @model_validator(mode="after")
    def validar_identificacion_por_tipo(cls, values):
        tipo = values.tipo_identificacion
        identificacion = values.identificacion

        if tipo in [TipoIdentificacion.CEDULA, TipoIdentificacion.RUC]:
            if not ValidacionCedulaRucService.es_identificacion_valida(identificacion):
                raise ValueError(f"La {tipo.value.lower()} ingresada no es válida.")
        elif tipo == TipoIdentificacion.PASAPORTE:
            if not identificacion or len(identificacion.strip()) < 5:
                raise ValueError("El pasaporte debe tener al menos 5 caracteres.")
        return values


class PersonaActualizar(BaseModel):
    identificacion: Optional[str] = None
    tipo_identificacion: Optional[TipoIdentificacion] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    ciudad: Optional[str] = None
    email: Optional[EmailStr] = None
    usuario_auditoria: str

    @model_validator(mode="after")
    def validar_identificacion_si_cambia(cls, values):
        tipo = values.tipo_identificacion
        identificacion = values.identificacion

        if identificacion and tipo:
            if tipo in [TipoIdentificacion.CEDULA, TipoIdentificacion.RUC]:
                if not ValidacionCedulaRucService.es_identificacion_valida(identificacion):
                    raise ValueError(f"La {tipo.value.lower()} ingresada no es válida.")
            elif tipo == TipoIdentificacion.PASAPORTE:
                if len(identificacion.strip()) < 5:
                    raise ValueError("El pasaporte debe tener al menos 5 caracteres.")
        elif identificacion or tipo:
            raise ValueError("Si vas a actualizar la identificación, debes enviar también el tipo.")
        return values


class PersonaRespuesta(PersonaBase):
    id: UUID
    activo: bool
    fecha_creacion: datetime
    fecha_modificacion: datetime
    usuario_auditoria: Optional[str]

    model_config = ConfigDict(from_attributes=True)
