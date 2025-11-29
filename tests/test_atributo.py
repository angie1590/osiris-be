from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from osiris.modules.inventario.atributo.repository import AtributoRepository
from osiris.modules.inventario.atributo.entity import Atributo, TipoDato


def test_atributo_repository_create_y_update():
    session = MagicMock()
    repo = AtributoRepository()

    created = repo.create(session, {"nombre": "color", "tipo_dato": TipoDato.STRING})
    assert isinstance(created, Atributo)
    session.add.assert_called_once()
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(created)

    # update parcial
    created.nombre = "color"
    updated = repo.update(session, created, {"nombre": "color2"})
    assert updated.nombre == "color2"
    session.commit.assert_called()
