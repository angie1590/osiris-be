from src.osiris.domain.service import BaseService
from .repository import TipoProductoRepository

class TipoProductoService(BaseService):
    repo = TipoProductoRepository()
