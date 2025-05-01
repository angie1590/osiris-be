# src/osiris/db/entities/persona_entidad.py

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from src.osiris.db.database import Base

from enum import Enum

class TipoIdentificacion(str, Enum):
    CEDULA = "CÉDULA"
    RUC = "RUC"
    PASAPORTE = "PASAPORTE"


class Persona(Base):
    __tablename__ = "tbl_persona"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo_identificacion: TipoIdentificacion
    tipo_identificacion = Column(String, nullable=False, default="CEDULA")
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    direccion = Column(String)
    telefono = Column(String)
    ciudad = Column(String)
    email = Column(String)

    # Auditoría
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_modificacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario_auditoria = Column(String, nullable=True)
