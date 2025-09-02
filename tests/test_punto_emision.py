# tests/unit/test_punto_emision_unit.py
from __future__ import annotations

from uuid import uuid4
from unittest.mock import MagicMock
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from src.osiris.modules.common.punto_emision.models import PuntoEmisionCreate, PuntoEmisionUpdate
from src.osiris.modules.common.punto_emision.entity import PuntoEmision
from src.osiris.modules.common.punto_emision.service import PuntoEmisionService
from src.osiris.modules.common.punto_emision.repository import PuntoEmisionRepository


# =======================
# DTOs: validaciones
# =======================

def test_punto_emision_create_ok():
    dto = PuntoEmisionCreate(
        codigo="002",
        descripcion="Caja 2",
        secuencial_actual=5,
        empresa_id=uuid4(),
        sucursal_id=uuid4(),
        usuario_auditoria="tester",
    )
    assert dto.codigo == "002"
    assert dto.secuencial_actual == 5


def test_punto_emision_create_codigo_invalido_falla():
    with pytest.raises(ValidationError):
        PuntoEmisionCreate(
            codigo="22",  # debe ser 3 chars
            descripcion="PE",
            empresa_id=uuid4(),
        )


# =======================
# Service: create valida FKs (empresa y sucursal)
# =======================

def test_punto_emision_service_create_empresa_not_found_404():
    session = MagicMock()
    # 1er check empresa -> None
    session.exec.return_value.first.return_value = None

    svc = PuntoEmisionService()
    svc.repo = MagicMock()

    payload = {
        "codigo": "010",
        "descripcion": "Caja 10",
        "empresa_id": uuid4(),
        "sucursal_id": None,
    }

    with pytest.raises(HTTPException) as exc:
        svc.create(session, payload)

    assert exc.value.status_code == 404
    assert "Empresa" in exc.value.detail
    svc.repo.create.assert_not_called()


def test_punto_emision_service_create_sucursal_not_found_404():
    session = MagicMock()
    # Simular dos consultas secuenciales: empresa ok, sucursal None
    first = MagicMock()
    second = MagicMock()
    first.first.return_value = object()   # empresa existe
    second.first.return_value = None      # sucursal no existe
    session.exec.side_effect = [first, second]

    svc = PuntoEmisionService()
    svc.repo = MagicMock()

    payload = {
        "codigo": "011",
        "descripcion": "Caja 11",
        "empresa_id": uuid4(),
        "sucursal_id": uuid4(),
    }

    with pytest.raises(HTTPException) as exc:
        svc.create(session, payload)

    assert exc.value.status_code == 404
    assert "Sucursal" in exc.value.detail
    svc.repo.create.assert_not_called()


def test_punto_emision_service_create_ok_llama_repo_create():
    session = MagicMock()
    # empresa existe, sucursal existe
    first = MagicMock()
    second = MagicMock()
    first.first.return_value = object()
    second.first.return_value = object()
    session.exec.side_effect = [first, second]

    svc = PuntoEmisionService()
    svc.repo = MagicMock()
    svc.repo.create.return_value = "PE_CREATED"

    payload = {
        "codigo": "012",
        "descripcion": "Caja 12",
        "empresa_id": uuid4(),
        "sucursal_id": uuid4(),
    }

    out = svc.create(session, payload)
    assert out == "PE_CREATED"
    svc.repo.create.assert_called_once()


# =======================
# Service: list_by_empresa_sucursal (paginado)
# =======================

def test_punto_emision_service_list_by_empresa_sucursal_retorna_items_y_meta():
    session = MagicMock()
    svc = PuntoEmisionService()
    svc.repo = MagicMock()
    svc.repo.list.return_value = (["p1", "p2", "p3"], 7)

    items, meta = svc.list_by_empresa_sucursal(
        session,
        empresa_id=uuid4(),
        sucursal_id=uuid4(),
        limit=3,
        offset=3,
        only_active=True,
    )

    assert items == ["p1", "p2", "p3"]
    assert meta.total == 7
    assert meta.limit == 3
    assert meta.offset == 3
    assert meta.has_more is True  # 7 > 6


# =======================
# Repository: delete lógico
# =======================

def test_punto_emision_repository_delete_logico():
    session = MagicMock()
    repo = PuntoEmisionRepository()

    obj = PuntoEmision(
        codigo="014",
        descripcion="PE 14",
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
