from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import date
from typing import Optional

class EmpleadoBase(BaseModel):
    salario: float = Field(gt=0)
    cargo: str
    fecha_ingreso: date
    fecha_nacimiento: Optional[date] = None
    fecha_salida: Optional[date] = None

class EmpleadoCrear(EmpleadoBase):
    id: UUID  # <- usamos directamente el ID heredado de persona
    usuario_auditoria: str

class EmpleadoActualizar(BaseModel):
    salario: Optional[float] = Field(default=None, gt=0)
    cargo: Optional[str] = None
    fecha_ingreso: Optional[date] = None
    fecha_nacimiento: Optional[date] = None
    fecha_salida: Optional[date] = None
    activo: Optional[bool] = None
    usuario_auditoria: str

class EmpleadoRespuesta(EmpleadoBase):
    id: UUID
    activo: bool
    usuario_auditoria: Optional[str]

    model_config = ConfigDict(from_attributes=True)