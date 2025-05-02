from sqlalchemy import Boolean, Column, Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.osiris.db.database import Base
from datetime import datetime

class Empleado(Base):
    __tablename__ = "tbl_empleado"

    id = Column(UUID(as_uuid=True), primary_key=True)  # FK con Persona
    salario = Column(Numeric(10, 2), nullable=False)
    cargo = Column(String, nullable=False)
    fecha_nacimiento = Column(Date, nullable=True)
    fecha_ingreso = Column(Date, nullable=False)
    fecha_salida = Column(Date, nullable=True)

    activo = Column(Boolean, default=True)
    fecha_creacion = Column(Date, default=datetime.now())
    fecha_modificacion = Column(Date, default=datetime.now(), onupdate=datetime.now())
    usuario_auditoria = Column(String, nullable=True)
