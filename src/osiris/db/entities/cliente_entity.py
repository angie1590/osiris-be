from sqlalchemy import Column, ForeignKey, Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from src.osiris.db.database import Base

class Cliente(Base):
    __tablename__ = "tbl_cliente"

    id = Column(UUID(as_uuid=True), primary_key=True)  # <- FK con persona
    tipo_cliente_id = Column(UUID(as_uuid=True), ForeignKey("aux_tipo_cliente.id"), nullable=False)

    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_modificacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario_auditoria = Column(String, nullable=True)

    tipo_cliente = relationship("TipoCliente", back_populates="clientes")