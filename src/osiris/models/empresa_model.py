"""
Modelos Pydantic que definen la estructura de entrada, salida y actualización
para los datos relacionados con la entidad Empresa, según los requerimientos
tributarios del SRI en Ecuador.
"""

from pydantic import BaseModel, ConfigDict, constr, field_validator
from uuid import UUID
from typing import Optional
from osiris.utils.validacion_identificacion import ValidacionCedulaRucService

class EmpresaBase(BaseModel):
    razon_social: constr(strip_whitespace=True, pattern=r'^[A-Za-zÁÉÍÓÚÑáéíóúñ\s]+$')
    nombre_comercial: Optional[constr(strip_whitespace=True, pattern=r'^[A-Za-zÁÉÍÓÚÑáéíóúñ0-9\s.,-]+$')] = None
    ruc: constr(min_length=13, max_length=13, pattern=r'^\d{13}$')
    direccion_matriz: str
    telefono: Optional[constr(pattern=r'^\d{7,10}$')] = None
    codigo_establecimiento: constr(min_length=3, max_length=3, pattern=r'^\d{3}$')
    obligado_contabilidad: bool
    tipo_contribuyente_id: str

    @field_validator('ruc')
    @classmethod
    def validar_ruc(cls, v):
        if not ValidacionCedulaRucService.es_identificacion_valida(v):
            raise ValueError('RUC o cédula no es válido según el algoritmo de validación')
        return v


class EmpresaCrear(EmpresaBase):
    """Modelo para la creación de una nueva empresa (matriz)."""
    pass


class EmpresaActualizar(BaseModel):
    """Modelo para la actualización parcial de los datos de una empresa."""
    razon_social: Optional[constr(strip_whitespace=True, pattern=r'^[A-Za-zÁÉÍÓÚÑáéíóúñ\s]+$')] = None
    nombre_comercial: Optional[constr(strip_whitespace=True, pattern=r'^[A-Za-zÁÉÍÓÚÑáéíóúñ0-9\s.,-]+$')] = None
    direccion_matriz: Optional[str] = None
    telefono: Optional[constr(pattern=r'^\d{7,10}$')] = None
    codigo_establecimiento: Optional[constr(min_length=3, max_length=3, pattern=r'^\d{3}$')] = None
    obligado_contabilidad: Optional[bool] = None
    tipo_contribuyente_id: Optional[str] = None


class EmpresaRespuesta(EmpresaBase):
    """Modelo de respuesta con información extendida de una empresa."""
    id: UUID
    activo: bool

    model_config = ConfigDict(from_attributes=True)
