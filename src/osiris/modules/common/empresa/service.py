from osiris.modules.sri.tipo_contribuyente.entity import TipoContribuyente
from src.osiris.domain.service import BaseService
from .repository import EmpresaRepository

class EmpresaService(BaseService):
    fk_models = {
        "tipo_contribuyente_codigo": (TipoContribuyente, "codigo"),
    }
    repo = EmpresaRepository()


