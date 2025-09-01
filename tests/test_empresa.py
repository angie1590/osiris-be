# tests/unit/test_empresa_unit.py
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.osiris.modules.common.empresa.models import EmpresaCreate, EmpresaUpdate
from src.osiris.modules.common.empresa.entity import Empresa
from src.osiris.modules.common.empresa.repository import EmpresaRepository
from src.osiris.modules.common.empresa.service import EmpresaService


# =======================
# DTO validations (Pydantic) – mock del validador de RUC
# =======================

def test_empresa_create_valida_usa_validador_ruc_ok():
    with patch(
        "src.osiris.modules.common.empresa.models.ValidacionCedulaRucService.es_identificacion_valida",
        return_value=True,
    ):
        dto = EmpresaCreate(
            razon_social="Comercial ABC",
            nombre_comercial="ABC S.A.",
            ruc="1104680138001",
            direccion_matriz="Av. Siempre Viva 123",
            telefono="0987654321",
            codigo_establecimiento="001",
            obligado_contabilidad=True,
            tipo_contribuyente_id="01",
            usuario_auditoria="tester",
        )
        assert dto.ruc == "1104680138001"
        assert dto.tipo_contribuyente_id == "01"


def test_empresa_create_ruc_invalido_lanza_validationerror():
    with patch(
        "src.osiris.modules.common.empresa.models.ValidacionCedulaRucService.es_identificacion_valida",
        return_value=False,
    ):
        with pytest.raises(ValidationError):
            EmpresaCreate(
                razon_social="Empresa XYZ",
                nombre_comercial="XYZ",
                ruc="0000000000000",
                direccion_matriz="Calle Falsa 123",
                telefono="022345678",
                codigo_establecimiento="001",
                obligado_contabilidad=False,
                tipo_contribuyente_id="01",
                usuario_auditoria="tester",
            )


def test_empresa_update_ruc_none_no_valida_y_es_permitido():
    # ruc es opcional en update; si va None no debe validarse
    # (no hace falta patch del validador)
    dto = EmpresaUpdate(ruc=None, telefono="022345678")
    assert dto.ruc is None
    assert dto.telefono == "022345678"


# =======================
# Repository (Session mock)
# =======================

def test_empresa_repository_create_desde_dict_instancia_y_persiste():
    session = MagicMock()
    repo = EmpresaRepository()

    payload = {
        "razon_social": "Mi Empresa",
        "nombre_comercial": "Mi Empresa Cía",
        "ruc": "1104680138001",
        "direccion_matriz": "Av. 123",
        "telefono": "022345678",
        "codigo_establecimiento": "001",
        "obligado_contabilidad": True,
        "tipo_contribuyente_id": "01",
        "usuario_auditoria": "tester",
        "activo": True,
    }

    created = repo.create(session, payload)
    assert isinstance(created, Empresa)
    assert created.razon_social == "Mi Empresa"
    session.add.assert_called_once()
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(created)


def test_empresa_repository_update_parcial_no_pisa_campos_no_enviados():
    session = MagicMock()
    repo = EmpresaRepository()

    db_obj = Empresa(
        razon_social="Original SA",
        nombre_comercial=None,
        ruc="1104680138001",
        direccion_matriz="Dir 1",
        telefono=None,
        codigo_establecimiento=None,
        obligado_contabilidad=False,
        tipo_contribuyente_id="01",
        usuario_auditoria="tester",
    )

    partial = EmpresaUpdate(
        nombre_comercial="Nuevo NC",  # no enviamos razon_social
        telefono="022345678",
    )

    updated = repo.update(session, db_obj, partial)

    assert updated.razon_social == "Original SA"     # se mantiene
    assert updated.nombre_comercial == "Nuevo NC"    # cambia
    assert updated.telefono == "022345678"           # cambia

    session.add.assert_called_once_with(db_obj)
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(db_obj)


def test_empresa_repository_delete_logico_activo_a_false():
    session = MagicMock()
    repo = EmpresaRepository()

    db_obj = Empresa(
        razon_social="Para Borrar",
        nombre_comercial=None,
        ruc="1104680138001",
        direccion_matriz="Dir",
        tipo_contribuyente_id="01",
        usuario_auditoria="tester",
        activo=True,
    )

    ok = repo.delete(session, db_obj)
    assert ok is True
    assert db_obj.activo is False
    session.add.assert_called_once_with(db_obj)
    session.delete.assert_not_called()
    session.commit.assert_called_once()


# =======================
# Service (repo mock)
# =======================

def test_empresa_service_update_not_found_devuelve_none():
    repo = MagicMock()
    repo.get.return_value = None

    s = EmpresaService()
    s.repo = repo

    out = s.update(MagicMock(), item_id=uuid4(), data={"razon_social": "X"})
    assert out is None
    repo.update.assert_not_called()


def test_empresa_service_update_found_llama_repo_update():
    repo = MagicMock()
    repo.get.return_value = object()
    repo.update.return_value = "UPDATED"

    s = EmpresaService()
    s.repo = repo

    out = s.update(MagicMock(), item_id=uuid4(), data={"razon_social": "Y"})
    assert out == "UPDATED"
    repo.update.assert_called_once()


def test_empresa_service_list_paginated_retorna_items_y_meta():
    repo = MagicMock()
    repo.list.return_value = (["e1", "e2"], 7)

    s = EmpresaService()
    s.repo = repo

    items, meta = s.list_paginated(MagicMock(), limit=2, offset=4, only_active=True)
    assert items == ["e1", "e2"]
    assert meta.total == 7
    assert meta.limit == 2
    assert meta.offset == 4
    assert meta.has_more is True
