from sqlalchemy import Column, ForeignKey, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from src.osiris.db.database import Base

class ProveedorPersona(Base):
    __tablename__ = "tbl_proveedor_persona"

    id = Column(UUID(as_uuid=True), primary_key=True)  # FK con Persona
    nombre_comercial = Column(String, nullable=True)
    tipo_contribuyente_id = Column(String(2), ForeignKey("aux_tipo_contribuyente.codigo"), nullable=False)

    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_modificacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario_auditoria = Column(String, nullable=True)

    tipo_contribuyente = relationship("TipoContribuyente")
