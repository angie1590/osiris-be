# src/modules/common/rol/service.py
from src.osiris.domain.service import BaseService
from .repository import RolRepository
from .models import Rol

class RolService(BaseService[Rol]):
    pass  # hooks disponibles si luego necesitas reglas
