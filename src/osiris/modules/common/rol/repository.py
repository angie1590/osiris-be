from src.osiris.domain.repository import BaseRepository
from .models import Rol

class RolRepository(BaseRepository):
    model = Rol