from sqlalchemy import Column, String, Boolean, DateTime, Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from src.osiris.db.database import Base
from enum import Enum

class TipoIdentificacion(str, Enum):
    CEDULA = "CEDULA"
    RUC = "RUC"
    PASAPORTE = "PASAPORTE"


class Persona(Base):
    __tablename__ = "tbl_persona"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo_identificacion = Column(
        SqlEnum(TipoIdentificacion, name="tipo_identificacion_enum", create_constraint=True),
        nullable=False,
        default=TipoIdentificacion.CEDULA
    )
    identificacion = Column(String, nullable=False, unique=True)
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