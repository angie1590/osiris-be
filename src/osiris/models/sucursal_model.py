# src/osiris/db/models/sucursal_modelo.py

from pydantic import BaseModel, ConfigDict, constr
from typing import Optional
from uuid import UUID


class SucursalBase(BaseModel):
    codigo: constr(min_length=3, max_length=3)
    nombre: str
    direccion: str
    telefono: Optional[str]
    empresa_id: UUID


class SucursalCrear(SucursalBase):
    pass


class SucursalActualizar(BaseModel):
    nombre: Optional[constr(strip_whitespace=True, min_length=3, max_length=50)] = None
    direccion: Optional[constr(strip_whitespace=True, min_length=3, max_length=100)] = None
    telefono: Optional[constr(strip_whitespace=True, pattern=r'^\d{7,10}$')] = None
    activo: Optional[bool] = True


class SucursalRespuesta(SucursalBase):
    id: UUID
    activo: bool

    model_config = ConfigDict(from_attributes=True)
