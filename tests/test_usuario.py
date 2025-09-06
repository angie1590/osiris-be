# tests/test_usuario.py
from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from src.osiris.modules.common.usuario.service import UsuarioService
from src.osiris.modules.common.usuario.models import UsuarioCreate, UsuarioUpdate


# -----------------------
# Helpers para sesión mock
# -----------------------

class _ResultFirst:
    """Wrapper para simular session.exec(...).first()."""
    def __init__(self, obj):
        self._obj = obj

    def first(self):
        return self._obj


def _mk_session_for_fk(persona_exists=True, persona_activa=True,
                       rol_exists=True, rol_activo=True):
    """
    Devuelve un Session mock cuyo .exec(stmt).first() retorna:
      - Persona (existe/activa según flags) cuando el stmt refiere a 'tbl_persona'
      - Rol (existe/activo según flags) cuando el stmt refiere a 'tbl_rol'
    """
    session = MagicMock()

    persona = None
    if persona_exists:
        persona = SimpleNamespace(id=uuid4(), activo=persona_activa)

    rol = None
    if rol_exists:
        rol = SimpleNamespace(id=uuid4(), activo=rol_activo)

    def _exec(stmt):
        s = str(stmt)
        if "tbl_persona" in s:
            return _ResultFirst(persona)
        if "tbl_rol" in s:
            return _ResultFirst(rol)
        # Para otros selects que no interesan en estos tests
        return _ResultFirst(None)

    session.exec.side_effect = _exec
    return session


# -----------------------
# Tests de CREATE
# -----------------------

def test_usuario_create_hash_password_y_valida_fks():
    session = _mk_session_for_fk(persona_exists=True, persona_activa=True,
                                 rol_exists=True, rol_activo=True)
    service = UsuarioService()
    service.repo = MagicMock()

    payload = UsuarioCreate(
        persona_id=uuid4(),
        rol_id=uuid4(),
        username="usuario1",
        password="Secreta123",
        usuario_auditoria="admin",
    )

    service.create(session, payload)

    # Verificamos que al repo le llega password_hash y NO password
    args, kwargs = service.repo.create.call_args
    assert args[0] is session
    sent = args[1]
    assert "password" not in sent
    assert "password_hash" in sent and isinstance(sent["password_hash"], str) and sent["password_hash"]


def test_usuario_create_con_persona_inexistente_404():
    session = _mk_session_for_fk(persona_exists=False, rol_exists=True, rol_activo=True)
    service = UsuarioService()
    service.repo = MagicMock()

    payload = UsuarioCreate(
        persona_id=uuid4(),
        rol_id=uuid4(),
        username="usuario1",
        password="Secreta123",
        usuario_auditoria="admin",
    )

    with pytest.raises(HTTPException) as exc:
        service.create(session, payload)
    assert exc.value.status_code == 404
    assert "Persona" in exc.value.detail


def test_usuario_create_con_rol_inactivo_409():
    session = _mk_session_for_fk(persona_exists=True, persona_activa=True,
                                 rol_exists=True, rol_activo=False)
    service = UsuarioService()
    service.repo = MagicMock()

    payload = UsuarioCreate(
        persona_id=uuid4(),
        rol_id=uuid4(),
        username="usuario1",
        password="Secreta123",
        usuario_auditoria="admin",
    )

    with pytest.raises(HTTPException) as exc:
        service.create(session, payload)
    assert exc.value.status_code in (409, 400)  # 409 recomendado; 400 si lo implementaste así
    assert "inactivo" in exc.value.detail.lower()


# -----------------------
# Tests de UPDATE
# -----------------------

def test_usuario_update_solo_rol_y_password_hash():
    session = _mk_session_for_fk(rol_exists=True, rol_activo=True)

    service = UsuarioService()
    service.repo = MagicMock()

    # El repo.get debe devolver algún objeto "existente"
    db_obj = SimpleNamespace(id=uuid4(), username="usuario1")
    service.repo.get.return_value = db_obj

    user_id = uuid4()
    upd = UsuarioUpdate(
        rol_id=uuid4(),
        password="NuevaClave!",
        usuario_auditoria="admin",
    )

    service.update(session, user_id, upd)

    # Verificamos que repo.update fue llamado con db_obj y sin 'password' en el dict
    args, kwargs = service.repo.update.call_args
    assert args[0] is session
    assert args[1] is db_obj
    sent = args[2]  # data dict
    assert "password" not in sent
    assert "password_hash" in sent and isinstance(sent["password_hash"], str) and sent["password_hash"]
    assert "rol_id" in sent
    # username/persona_id NO deben ir en update
    assert "username" not in sent
    assert "persona_id" not in sent


def test_usuario_update_sin_password_no_rehash():
    session = _mk_session_for_fk(rol_exists=True, rol_activo=True)

    service = UsuarioService()
    service.repo = MagicMock()
    service.repo.get.return_value = SimpleNamespace(id=uuid4())

    upd = UsuarioUpdate(rol_id=uuid4(), usuario_auditoria="editor")
    service.update(session, uuid4(), upd)

    # Si no llega password, no debe viajar 'password_hash'
    args, kwargs = service.repo.update.call_args
    sent = args[2]
    assert "password_hash" not in sent


def test_usuario_update_rol_inactivo_409():
    session = _mk_session_for_fk(rol_exists=True, rol_activo=False)

    service = UsuarioService()
    service.repo = MagicMock()
    service.repo.get.return_value = SimpleNamespace(id=uuid4())

    upd = UsuarioUpdate(rol_id=uuid4(), usuario_auditoria="editor")

    with pytest.raises(HTTPException) as exc:
        service.update(session, uuid4(), upd)
    assert exc.value.status_code in (409, 400)
    assert "inactivo" in exc.value.detail.lower()


def test_usuario_update_inexistente_devuelve_none():
    session = _mk_session_for_fk(rol_exists=True, rol_activo=True)

    service = UsuarioService()
    service.repo = MagicMock()
    service.repo.get.return_value = None  # no existe

    upd = UsuarioUpdate(rol_id=uuid4(), usuario_auditoria="editor")
    assert service.update(session, uuid4(), upd) is None
