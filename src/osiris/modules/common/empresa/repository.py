from src.osiris.domain.repository import BaseRepository
from .entity import Empresa

class EmpresaRepository(BaseRepository):
    model = Empresa
