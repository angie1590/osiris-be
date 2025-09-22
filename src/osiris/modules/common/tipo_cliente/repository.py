from __future__ import annotations

from src.osiris.domain.repository import BaseRepository
from .entity import TipoCliente


class TipoClienteRepository(BaseRepository):
    model = TipoCliente
