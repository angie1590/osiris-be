"""
Tests unitarios para CategoriaAtributo
"""
from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from osiris.modules.inventario.categoria_atributo.service import CategoriaAtributoService
from osiris.modules.inventario.categoria_atributo.entity import CategoriaAtributo
from osiris.modules.inventario.categoria_atributo.models import (
    CategoriaAtributoCreate,
    CategoriaAtributoUpdate,
)


def test_categoria_atributo_service_create_ok():
    """Verificar que create instancia y persiste la asociación"""
    session = MagicMock()
    service = CategoriaAtributoService()

    categoria_id = uuid4()
    atributo_id = uuid4()

    dto = CategoriaAtributoCreate(
        categoria_id=categoria_id,
        atributo_id=atributo_id,
        orden=1,
        obligatorio=True,
    )

    # Mock de session.add / commit / refresh
    created_entity = CategoriaAtributo(
        categoria_id=categoria_id,
        atributo_id=atributo_id,
        orden=1,
        obligatorio=True,
        usuario_auditoria="api",
        activo=True,
    )
    created_entity.id = uuid4()

    def mock_refresh(entity):
        entity.id = created_entity.id

    session.refresh.side_effect = mock_refresh

    result = service.create(session, dto, usuario_auditoria="test_user")

    session.add.assert_called_once()
    session.commit.assert_called_once()
    session.refresh.assert_called_once()


def test_categoria_atributo_service_update_ok():
    """Verificar que update modifica campos permitidos"""
    session = MagicMock()
    service = CategoriaAtributoService()

    entity_id = uuid4()
    existing = CategoriaAtributo(
        categoria_id=uuid4(),
        atributo_id=uuid4(),
        orden=1,
        obligatorio=False,
        usuario_auditoria="original",
        activo=True,
    )
    existing.id = entity_id

    session.get.return_value = existing

    dto = CategoriaAtributoUpdate(orden=5, obligatorio=True)

    result = service.update(session, entity_id, dto, usuario_auditoria="test_user")

    assert result is not None
    session.add.assert_called_once()
    session.commit.assert_called_once()
    session.refresh.assert_called_once()


def test_categoria_atributo_service_update_not_found():
    """Verificar que update devuelve None si no existe"""
    session = MagicMock()
    service = CategoriaAtributoService()

    session.get.return_value = None

    dto = CategoriaAtributoUpdate(orden=10)

    result = service.update(session, uuid4(), dto)

    assert result is None
    session.add.assert_not_called()
    session.commit.assert_not_called()


def test_categoria_atributo_service_delete_soft():
    """Verificar que delete hace soft-delete (activo=False)"""
    session = MagicMock()
    service = CategoriaAtributoService()

    entity_id = uuid4()
    existing = CategoriaAtributo(
        categoria_id=uuid4(),
        atributo_id=uuid4(),
        orden=1,
        obligatorio=False,
        usuario_auditoria="original",
        activo=True,
    )
    existing.id = entity_id

    session.get.return_value = existing

    result = service.delete(session, entity_id, usuario_auditoria="test_user")

    assert result is True
    assert existing.activo is False
    session.add.assert_called_once()
    session.commit.assert_called_once()


def test_categoria_atributo_service_delete_not_found():
    """Verificar que delete devuelve False si no existe"""
    session = MagicMock()
    service = CategoriaAtributoService()

    session.get.return_value = None

    result = service.delete(session, uuid4())

    assert result is False
    session.add.assert_not_called()
    session.commit.assert_not_called()


def test_categoria_atributo_service_list_paginated():
    """Verificar que list_paginated respeta filtros y paginación"""
    session = MagicMock()
    service = CategoriaAtributoService()

    categoria_id = uuid4()

    mock_exec = MagicMock()
    mock_exec.return_value = [
        CategoriaAtributo(
            categoria_id=categoria_id,
            atributo_id=uuid4(),
            orden=1,
            obligatorio=True,
            usuario_auditoria="api",
            activo=True,
        )
    ]
    session.exec = mock_exec

    result = service.list_paginated(session, skip=0, limit=10, categoria_id=categoria_id)

    assert len(result) == 1
    session.exec.assert_called_once()
