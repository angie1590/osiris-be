from sqlalchemy import Column, String, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from src.osiris.db.database import Base

class TipoCliente(Base):
    __tablename__ = "aux_tipo_cliente"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String, unique=True, nullable=False)
    descuento = Column(Numeric(5, 2), nullable=False)

    clientes = relationship("Cliente", back_populates="tipo_cliente")
