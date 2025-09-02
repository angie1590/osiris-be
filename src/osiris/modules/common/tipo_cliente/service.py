from __future__ import annotations

from src.osiris.domain.service import BaseService
from .repository import TipoClienteRepository


class TipoClienteService(BaseService):
    repo = TipoClienteRepository()
