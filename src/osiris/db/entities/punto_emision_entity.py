# src/osiris/db/entities/punto_emision_entidad.py

from datetime import datetime
from sqlalchemy import Column, DateTime, String, Boolean, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.osiris.db.database import Base
import uuid


class PuntoEmision(Base):
    __tablename__ = "tbl_punto_emision"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(3), nullable=False)
    descripcion = Column(String, nullable=False)
    secuencial_actual = Column(Integer, default=1)
    activo = Column(Boolean, default=True)

    fecha_creacion = Column(DateTime, default=datetime.now())
    fecha_modificacion = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    usuario_auditoria = Column(String, nullable=True)

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("tbl_empresa.id"), nullable=False)
    sucursal_id = Column(UUID(as_uuid=True), ForeignKey("tbl_sucursal.id"), nullable=True)

    empresa = relationship("Empresa", back_populates="puntos_emision")
    sucursal = relationship("Sucursal", back_populates="puntos_emision")

    __table_args__ = (
        UniqueConstraint('codigo', 'empresa_id', 'sucursal_id', name='uq_codigo_por_entidad'),
    )
