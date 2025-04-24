# src/osiris/db/entities/sucursal_entidad.py

from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.osiris.db.database import Base
import uuid


class Sucursal(Base):
    __tablename__ = "tbl_sucursal"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(3), nullable=False)
    nombre = Column(String, nullable=False)
    direccion = Column(String, nullable=False)
    telefono = Column(String)
    activo = Column(Boolean, default=True)

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("tbl_empresa.id"), nullable=False)
    empresa = relationship("Empresa", back_populates="sucursales")
    puntos_emision = relationship("PuntoEmision", back_populates="sucursal")
