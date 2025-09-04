# src/osiris/modules/common/usuario/service.py
from __future__ import annotations

from typing import Any
from fastapi import HTTPException
from sqlmodel import Session, select

from src.osiris.domain.service import BaseService
from src.osiris.core import security
from .repository import UsuarioRepository
from .entity import Usuario
from src.osiris.modules.common.persona.entity import Persona

from src.osiris.modules.common.rol.entity import Rol


class UsuarioService(BaseService):
    fk_models = {
        "persona_id": Persona,
        "rol_id": Rol,
    }
    def __init__(self, repo: UsuarioRepository | None = None) -> None:
        self.repo = repo or UsuarioRepository()

    @staticmethod
    def _ensure_dict(data: Any) -> dict[str, Any]:
        if hasattr(data, "model_dump"):
            return data.model_dump(exclude_unset=True)  # pydantic/sqlmodel v2
        if isinstance(data, dict):
            return data
        return {k: v for k, v in vars(data).items() if not k.startswith("_")}

    @staticmethod
    def _pop_and_hash_password(data: dict[str, Any]) -> None:
        plain = data.pop("password", None)
        if plain:
            data["password_hash"] = security.hash_password(plain)

    def _check_uniques(self, session: Session, data: dict[str, Any], exclude_id: Any | None = None) -> None:
        # username/persona_id no vienen en update (ver UsuarioUpdate), pero sí en create
        if "username" in data and data["username"] is not None:
            stmt = select(Usuario).where(Usuario.username == data["username"])
            if exclude_id:
                stmt = stmt.where(Usuario.id != exclude_id)
            if session.exec(stmt).first():
                raise HTTPException(status_code=409, detail="El nombre de usuario ya existe")

        if "persona_id" in data and data["persona_id"] is not None:
            stmt = select(Usuario).where(Usuario.persona_id == data["persona_id"])
            if exclude_id:
                stmt = stmt.where(Usuario.id != exclude_id)
            if session.exec(stmt).first():
                raise HTTPException(status_code=409, detail="La persona ya tiene usuario asignado")

    def _check_fk_existence(self, session: Session, data: dict[str, Any]) -> None:
        persona_id = data.get("persona_id")
        if persona_id:
            if not session.exec(select(Persona).where(Persona.id == persona_id)).first():
                raise HTTPException(status_code=404, detail="Persona no encontrada")

        rol_id = data.get("rol_id")
        if rol_id:
            if not session.exec(select(Rol).where(Rol.id == rol_id)).first():
                raise HTTPException(status_code=404, detail="Rol no encontrado")

    # --------- CREATE ----------
    def create(self, session: Session, data: Any) -> Usuario:
        data = self._ensure_dict(data)
        self._check_fk_existence(session, data)
        self._check_uniques(session, data)
        self._pop_and_hash_password(data)
        if not data.get("password_hash"):
            raise HTTPException(status_code=400, detail="La contraseña es obligatoria")
        data.setdefault("requiere_cambio_password", True)
        return super().create(session, data)

    # --------- UPDATE (solo rol_id, password, usuario_auditoria) ----------
    def update(self, session: Session, obj_id: Any, data: Any) -> Usuario | None:
        incoming = self._ensure_dict(data)

        # 🔒 Filtrar estrictamente los campos permitidos en update
        allowed = {"rol_id", "password", "usuario_auditoria"}
        data = {k: v for k, v in incoming.items() if k in allowed and v is not None}

        # Validar rol si viene
        if "rol_id" in data:
            self._check_fk_existence(session, {"rol_id": data["rol_id"]})

        # Hash si llega password
        self._pop_and_hash_password(data)

        # No hay unicidad que comprobar aquí (username/persona_id no cambian)
        return super().update(session, obj_id, data)

    # --------- opcional: autenticación ----------
    def authenticate(self, session: Session, username: str, password: str) -> Usuario | None:
        user = session.exec(select(Usuario).where(Usuario.username == username)).first()
        if not user:
            return None
        from src.osiris.core import security as _sec
        if not _sec.verify_password(password, user.password_hash):
            return None
        return user
