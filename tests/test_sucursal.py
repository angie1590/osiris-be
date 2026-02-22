# tests/unit/test_sucursal_unit.py
from __future__ import annotations

from uuid import uuid4
from unittest.mock import MagicMock
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine

from osiris.modules.common.sucursal.models import SucursalCreate, SucursalUpdate
from osiris.modules.common.sucursal.entity import Sucursal
from osiris.modules.common.sucursal.service import SucursalService
from osiris.modules.common.sucursal.repository import SucursalRepository


# =======================
# DTOs: validaciones
# =======================

def test_sucursal_create_ok():
    dto = SucursalCreate(
        codigo="001",
        nombre="Sucursal Centro",
        direccion="Av. Principal 123",
        telefono="022345678",
        empresa_id=uuid4(),
        usuario_auditoria="tester",
    )
    assert dto.codigo == "001"
    assert dto.nombre.startswith("Sucursal")
    assert dto.telefono == "022345678"


def test_sucursal_create_codigo_invalido_falla():
    with pytest.raises(ValidationError):
        SucursalCreate(
            codigo="1",  # debe ser 3 chars
            nombre="Suc",
            direccion="Dir",
            empresa_id=uuid4(),
            usuario_auditoria="tester",
        )


def test_sucursal_update_parcial_ok():
    dto = SucursalUpdate(
        nombre="Nuevo Nombre",
        telefono="0987654321",
    )
    assert dto.nombre == "Nuevo Nombre"
    assert dto.telefono == "0987654321"


# =======================
# Service: create valida FK empresa
# =======================

def test_sucursal_service_create_empresa_not_found_404():
    session = MagicMock()
    session.exec.return_value.first.return_value = None  # Empresa no existe

    svc = SucursalService()

    payload = {
        "codigo": "001",
        "nombre": "Sucursal X",
        "direccion": "Dir",
        "empresa_id": uuid4(),
    }

    with pytest.raises(HTTPException) as exc:
        svc.create(session, payload)

    assert exc.value.status_code == 404
    assert "Empresa" in exc.value.detail


def test_sucursal_service_create_ok_commit_y_refresh():
    session = MagicMock()
    session.exec.return_value.first.return_value = object()  # Empresa existe

    svc = SucursalService()

    payload = {
        "codigo": "001",
        "nombre": "Sucursal X",
        "direccion": "Dir",
        "usuario_auditoria": "tester",
        "empresa_id": uuid4(),
    }

    out = svc.create(session, payload)
    assert out.codigo == "001"
    session.add.assert_called_once()
    session.commit.assert_called_once()
    session.refresh.assert_called_once()


def test_sucursal_service_create_duplica_codigo_devuelve_400():
    session = MagicMock()
    session.exec.return_value.first.return_value = object()  # Empresa existe
    session.commit.side_effect = IntegrityError(
        statement="INSERT INTO tbl_sucursal ...",
        params={},
        orig=Exception("duplicate key value violates unique constraint uq_sucursal_empresa_codigo"),
    )
    svc = SucursalService()

    payload = {
        "codigo": "002",
        "nombre": "Sucursal Sur",
        "direccion": "Dir",
        "usuario_auditoria": "tester",
        "empresa_id": uuid4(),
    }

    with pytest.raises(HTTPException) as exc:
        svc.create(session, payload)

    assert exc.value.status_code == 400
    assert exc.value.detail == "La empresa ya posee una sucursal con ese código"
    session.rollback.assert_called_once()


# =======================
# Service: list_by_empresa (paginado)
# =======================

def test_sucursal_service_list_by_empresa_retorna_items_y_meta():
    session = MagicMock()
    svc = SucursalService()
    svc.repo = MagicMock()
    svc.repo.list.return_value = (["s1", "s2"], 5)

    items, meta = svc.list_by_empresa(
        session,
        empresa_id=uuid4(),
        limit=2,
        offset=0,
        only_active=True,
    )

    assert items == ["s1", "s2"]
    assert meta.total == 5
    assert meta.limit == 2
    assert meta.offset == 0
    assert meta.has_more is True  # 5 > 2


# =======================
# Repository: delete lógico
# =======================

def test_sucursal_repository_delete_logico():
    session = MagicMock()
    repo = SucursalRepository()

    obj = Sucursal(
        codigo="013",
        nombre="Suc",
        direccion="Dir",
        empresa_id=uuid4(),
        usuario_auditoria="tester",
        activo=True,
    )
    ok = repo.delete(session, obj)
    assert ok is True
    assert obj.activo is False
    session.add.assert_called_once_with(obj)
    session.commit.assert_called_once()
    # opcional: garantizar que no refrescamos
    session.refresh.assert_not_called()


def _engine_sqlite():
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def test_sucursal_codigo_unico_por_empresa():
    engine = _engine_sqlite()
    Sucursal.__table__.create(bind=engine)
    empresa_id = uuid4()

    with Session(engine) as session:
        session.add(
            Sucursal(
                codigo="002",
                nombre="Sucursal Norte",
                direccion="Quito",
                es_matriz=False,
                empresa_id=empresa_id,
            )
        )
        session.commit()

        session.add(
            Sucursal(
                codigo="002",
                nombre="Sucursal Duplicada",
                direccion="Quito",
                es_matriz=False,
                empresa_id=empresa_id,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_sucursal_matriz_solo_puede_ser_001():
    engine = _engine_sqlite()
    Sucursal.__table__.create(bind=engine)

    with Session(engine) as session:
        session.add(
            Sucursal(
                codigo="002",
                nombre="Sucursal Incorrecta",
                direccion="Guayaquil",
                es_matriz=True,
                empresa_id=uuid4(),
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
