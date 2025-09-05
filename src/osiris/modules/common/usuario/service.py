# src/osiris/modules/common/usuario/service.py
from __future__ import annotations

from typing import Any
from fastapi import HTTPException
from sqlmodel import Session, select
from uuid import UUID

from src.osiris.domain.service import BaseService
from src.osiris.core import security
from .repository import UsuarioRepository
from .entity import Usuario
from src.osiris.modules.common.persona.entity import Persona
from src.osiris.modules.common.rol.entity import Rol


class UsuarioService(BaseService):
    """
    - Validación de FKs (persona_id, rol_id) se hace en BaseService usando fk_models.
    - Unicidades (username, persona_id único) se delegan al BaseRepository (maneja IntegrityError -> 409).
    - Reglas de negocio aquí: hash de password, campos no editables en update.
    """
    repo = UsuarioRepository()
    fk_models = {
        "persona_id": Persona,
        "rol_id": Rol,
    }

    # ---------- helpers ----------
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

    # ---------- CREATE ----------
    def create(self, session: Session, data: Any) -> Usuario:
        data = self._ensure_dict(data)

        # Hash obligatorio en create
        self._pop_and_hash_password(data)
        if not data.get("password_hash"):
            raise HTTPException(status_code=400, detail="La contraseña es obligatoria")

        # Reglas por defecto
        data.setdefault("requiere_cambio_password", True)

        # BaseService hará:
        # - validate_create (si lo sobreescribes)
        # - _check_fk_active_and_exists (con fk_models)
        # - repo.create (que captura IntegrityError y mapea a 409)
        return super().create(session, data)

    # ---------- UPDATE (solo rol_id, password, usuario_auditoria) ----------
    def update(self, session: Session, item_id: UUID, data: Any) -> Usuario | None:
        incoming = self._ensure_dict(data)

        # 🔒 Campos permitidos en update
        allowed = {"rol_id", "password", "usuario_auditoria"}
        data = {k: v for k, v in incoming.items() if k in allowed and v is not None}

        # Hash si viene password
        self._pop_and_hash_password(data)

        # Nota: BaseService._check_fk_active_and_exists validará rol_id si viene en 'data'
        # Unicidades no aplican aquí (username/persona_id no cambian)

        return super().update(session, item_id, data)

    # ---------- Auth opcional ----------
    def authenticate(self, session: Session, username: str, password: str) -> Usuario | None:
        user = session.exec(select(Usuario).where(Usuario.username == username)).first()
        if not user:
            return None
        if not security.verify_password(password, user.password_hash):
            return None
        return user
