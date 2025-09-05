from src.osiris.domain.repository import BaseRepository
from .entity import Cargo

class CargoRepository(BaseRepository):
    model = Cargo