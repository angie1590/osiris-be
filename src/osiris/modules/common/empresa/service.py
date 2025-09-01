from src.osiris.domain.service import BaseService
from .repository import EmpresaRepository

class EmpresaService(BaseService):
    repo = EmpresaRepository()
