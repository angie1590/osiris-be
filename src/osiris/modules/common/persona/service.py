# src/osiris/modules/common/persona/service.py
from __future__ import annotations

from typing import Any
from fastapi import HTTPException
from sqlmodel import Session, select

from src.osiris.domain.service import BaseService
from .repository import PersonaRepository
from .entity import Persona


class PersonaService(BaseService):
    def __init__(self, repo: PersonaRepository | None = None) -> None:
        self.repo = repo or PersonaRepository()

    # Si necesitas lógica extra en update, déjala aquí. Por defecto usamos la base:
    # def update(self, session: Session, obj_id: Any, data: dict[str, Any]) -> Persona | None:
    #     return super().update(session, obj_id, data)
