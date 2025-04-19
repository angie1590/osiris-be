"""
Entidad SQLAlchemy que representa la tabla `tbl_empresa` en la base de datos,
correspondiente a la empresa matriz registrada ante el SRI. Contiene los datos
tributarios exigidos y sus relaciones con sucursales y puntos de emisión.
"""

from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.osiris.db.database import Base
import uuid


class Empresa(Base):
    """
    Entidad que representa a una empresa matriz.
    Incluye información tributaria y relaciones con puntos de emisión y sucursales.
    """
    __tablename__ = "tbl_empresa"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    razon_social = Column(String, nullable=False)
    nombre_comercial = Column(String)
    ruc = Column(String(13), unique=True, nullable=False, index=True)
    direccion_matriz = Column(String, nullable=False)
    telefono = Column(String)
    codigo_establecimiento = Column(String(3), nullable=False)
    obligado_contabilidad = Column(Boolean, nullable=False, default=False)
    tipo_contribuyente_id = Column(UUID(as_uuid=True), ForeignKey("aux_tipo_contribuyente.id"))
    activo = Column(Boolean, default=True)

    tipo_contribuyente = relationship("TipoContribuyente")
    sucursales = relationship("Sucursal", back_populates="empresa")
    puntos_emision = relationship("PuntoEmision", back_populates="empresa")
