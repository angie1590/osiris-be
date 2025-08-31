# src/modules/common/rol/repository.py
from src.osiris.domain.repository import BaseRepository
from .models import Rol

class RolRepository(BaseRepository[Rol]):
    model = Rol
