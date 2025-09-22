# tests/unit/test_tipo_cliente_unit.py
from __future__ import annotations

from unittest.mock import MagicMock
import pytest
from pydantic import ValidationError

from osiris.modules.common.tipo_cliente.models import (
    TipoClienteCreate,
    TipoClienteUpdate,
)
from osiris.modules.common.tipo_cliente.entity import TipoCliente
from osiris.modules.common.tipo_cliente.service import TipoClienteService
from osiris.modules.common.tipo_cliente.repository import TipoClienteRepository


# ============================================================
# DTOs: validaciones
# ============================================================

def test_tipo_cliente_create_ok():
    dto = TipoClienteCreate(
        nombre="Preferente",
        descuento=15,
        usuario_auditoria="tester",
    )
    assert dto.descuento == 15


@pytest.mark.parametrize("valor", [-1, 101, 50.5])
def test_tipo_cliente_create_descuento_fuera_de_rango_falla(valor):
    with pytest.raises(ValidationError):
        TipoClienteCreate(
            nombre="Invalido",
            descuento=valor,
            usuario_auditoria="tester",
        )


def test_tipo_cliente_update_parcial_ok():
    dto = TipoClienteUpdate(
        descuento=0.0,
        # si tu Update exige usuario_auditoria, descomenta:
        # usuario_auditoria="tester",
    )
    assert dto.descuento == 0.0


# ============================================================
# Service: list_paginated (usa repo.list -> (items, total))
# ============================================================

def test_tipo_cliente_service_list_paginated_retorna_items_y_meta():
    session = MagicMock()
    service = TipoClienteService()
    service.repo = MagicMock()
    service.repo.list.return_value = (
        [TipoCliente(nombre="A", descuento=10.0),
         TipoCliente(nombre="B", descuento=5.0)],
        7,  # total
    )

    items, meta = service.list_paginated(
        session,
        limit=2,
        offset=0,
        only_active=True,
    )

    assert len(items) == 2
    assert isinstance(items[0], TipoCliente)
    assert meta.total == 7
    assert meta.limit == 2
    assert meta.offset == 0
    assert meta.has_more is True  # 7 > 2


# ============================================================
# Repository: delete lógico
# ============================================================

def test_tipo_cliente_repository_delete_logico():
    session = MagicMock()
    repo = TipoClienteRepository()

    obj = TipoCliente(
        nombre="Temporal",
        descuento=10.0,
        usuario_auditoria="tester",
        activo=True,
    )

    ok = repo.delete(session, obj)

    assert ok is True
    assert obj.activo is False
    session.add.assert_called_once_with(obj)
    session.commit.assert_called_once()
    session.refresh.assert_not_called()