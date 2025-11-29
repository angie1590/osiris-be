from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from osiris.modules.inventario.tipo_producto.repository import TipoProductoRepository
from osiris.modules.inventario.tipo_producto.entity import TipoProducto


def test_tipo_producto_repository_create_and_update():
    session = MagicMock()
    repo = TipoProductoRepository()

    data = {
        "producto_id": uuid4(),
        "atributo_id": uuid4(),
        "orden": 1,
        "obligatorio": True,
    }

    created = repo.create(session, data)
    assert isinstance(created, TipoProducto)
    session.add.assert_called_once()
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(created)

    # update parcial
    created.orden = 1
    updated = repo.update(session, created, {"orden": 2, "obligatorio": False})
    assert updated.orden == 2
    assert updated.obligatorio is False
    assert session.commit.called
