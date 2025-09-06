# src/osiris/modules/common/empleado/repository.py
from __future__ import annotations

from src.osiris.domain.repository import BaseRepository
from .entity import Empleado


class EmpleadoRepository(BaseRepository):
    model = Empleado
