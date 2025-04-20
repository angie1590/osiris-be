"""
Modelos Pydantic que definen la estructura de entrada, salida y actualización
para los datos relacionados con la entidad Empresa, según los requerimientos
tributarios del SRI en Ecuador.
"""

from pydantic import BaseModel, ConfigDict, constr
from uuid import UUID
from typing import Optional


class EmpresaBase(BaseModel):
    """
    Modelo base para la entidad Empresa.
    Define atributos requeridos por el SRI para la compañía matriz.
    """
    razon_social: constr(strip_whitespace=True, min_length=3)
    nombre_comercial: Optional[constr(strip_whitespace=True, min_length=3)] = None
    ruc: constr(min_length=13, max_length=13)
    direccion_matriz: str
    telefono: Optional[str] = None
    codigo_establecimiento: constr(min_length=3, max_length=3)
    obligado_contabilidad: bool
    tipo_contribuyente_id: str


class EmpresaCrear(EmpresaBase):
    """Modelo para la creación de una nueva empresa (matriz)."""
    pass


class EmpresaActualizar(BaseModel):
    """Modelo para la actualización parcial de los datos de una empresa."""
    razon_social: Optional[str]
    nombre_comercial: Optional[str]
    direccion_matriz: Optional[str]
    telefono: Optional[str]
    codigo_establecimiento: Optional[str]
    obligado_contabilidad: Optional[bool]
    tipo_contribuyente_id: Optional[str]


class EmpresaRespuesta(EmpresaBase):
    """Modelo de respuesta con información extendida de una empresa."""
    id: UUID
    activo: bool

    model_config = ConfigDict(from_attributes=True)
