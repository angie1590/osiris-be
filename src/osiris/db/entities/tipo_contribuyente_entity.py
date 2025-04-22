# src/osiris/db/entities/tipo_contribuyente_entidad.py

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from src.osiris.db.database import Base


class TipoContribuyente(Base):
    __tablename__ = "aux_tipo_contribuyente"

    codigo = Column(String(2), primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)

    empresas = relationship("Empresa", back_populates="tipo_contribuyente")
