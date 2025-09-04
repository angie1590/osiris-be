# src/osiris/modules/common/usuario/repository.py
from __future__ import annotations
from src.osiris.domain.repository import BaseRepository
from .entity import Usuario

class UsuarioRepository(BaseRepository):
    model = Usuario
