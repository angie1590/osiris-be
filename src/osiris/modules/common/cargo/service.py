from src.osiris.domain.service import BaseService
from .repository import CargoRepository

class CargoService(BaseService):
    repo = CargoRepository()
    pass  # hooks disponibles si luego necesitas reglas
