from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from src.osiris.db.database import Base
import uuid

class Rol(Base):
    __tablename__ = "tbl_rol"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(String)

    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now())
    fecha_modificacion = Column(DateTime, default=datetime.now(), onupdate=datetime.utcnow)
    usuario_auditoria = Column(String, nullable=True)

    usuarios = relationship("Usuario", back_populates="rol")
