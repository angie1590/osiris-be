from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from src.osiris.db.database import Base
import uuid

class ProveedorSociedad(Base):
    __tablename__ = "tbl_proveedor_sociedad"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ruc = Column(String, unique=True,nullable=False)
    razon_social = Column(String, nullable=False)
    direccion = Column(String, nullable=False)
    telefono = Column(String, nullable=True)
    email = Column(String, nullable=False)

    tipo_contribuyente_id = Column(String(2), ForeignKey("aux_tipo_contribuyente.id"), nullable=False)
    persona_contacto_id = Column(UUID(as_uuid=True), ForeignKey("tbl_persona.id"), nullable=False)

    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    fecha_modificacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario_auditoria = Column(String, nullable=True)

    tipo_contribuyente = relationship("TipoContribuyente")