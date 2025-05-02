from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.osiris.db.database import Base

class Usuario(Base):
    __tablename__ = "tbl_usuario"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("tbl_persona.id"), unique=True, nullable=False)
    rol_id = Column(UUID(as_uuid=True), ForeignKey("tbl_rol.id"), nullable=False)

    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    requiere_cambio_password = Column(Boolean, default=True)

    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now())
    fecha_modificacion = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    usuario_auditoria = Column(String, nullable=True)

    rol = relationship("Rol", back_populates="usuarios")
