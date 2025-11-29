from osiris.domain.repository import BaseRepository
from .entity import TipoProducto

class TipoProductoRepository(BaseRepository):
    model = TipoProducto
