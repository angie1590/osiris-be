from __future__ import annotations

from src.osiris.domain.repository import BaseRepository
from .entity import ProveedorPersona


class ProveedorPersonaRepository(BaseRepository):
    model = ProveedorPersona