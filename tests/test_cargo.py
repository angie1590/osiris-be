from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import BaseModel

# Repositorio/Servicio reales (no tocan BD porque mockeamos Session / repo)
from src.osiris.modules.common.cargo.repository import CargoRepository
from src.osiris.modules.common.cargo.service import CargoService
from src.osiris.modules.common.cargo.entity import Cargo
from src.osiris.modules.common.cargo.models import CargoUpdate


# ---------------------------
# Repositorio: create / update / delete (con Session mock)
# ---------------------------

def test_cargo_repository_create_desde_dict_instancia_modelo_y_persiste():
    session = MagicMock()
    repo = CargoRepository()

    payload = {"nombre": f"Cargo-{uuid4().hex[:8]}", "usuario_auditoria": "tester"}
    created = repo.create(session, payload)

    assert isinstance(created, Cargo)
    assert created.nombre == payload["nombre"]
    session.add.assert_called_once()            # se envía a la sesión
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(created)


def test_cargo_repository_create_desde_pydantic_instancia_modelo():
    session = MagicMock()
    repo = CargoRepository()

    class CargoCreateDTO(BaseModel):
        nombre: str
        usuario_auditoria: str | None = None

    dto = CargoCreateDTO(nombre=f"Cargo-{uuid4().hex[:8]}", usuario_auditoria="tester")
    created = repo.create(session, dto)

    assert isinstance(created, Cargo)
    assert created.nombre == dto.nombre
    session.add.assert_called_once()
    session.commit.assert_called_once()
    session.refresh.assert_called_once()


def test_cargo_repository_update_desde_dict_actualiza_campos():
    session = MagicMock()
    repo = CargoRepository()

    db_obj = Cargo(nombre="Viejo", usuario_auditoria="tester")
    data = {"nombre": "Nuevo"}

    updated = repo.update(session, db_obj, data)

    assert updated.nombre == "Nuevo"
    session.add.assert_called_once_with(db_obj)
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(db_obj)


def test_cargo_repository_update_desde_pydantic_exclude_unset():
    session = MagicMock()
    repo = CargoRepository()

    db_obj = Cargo(nombre="Original",usuario_auditoria="tester")
    dto = CargoUpdate(nombre="Actualizado")

    updated = repo.update(session, db_obj, dto)

    assert updated.nombre == "Actualizado"
    session.commit.assert_called_once()


def test_cargo_repository_delete_logico_si_tiene_activo():
    session = MagicMock()
    repo = CargoRepository()

    db_obj = Cargo(nombre="X", usuario_auditoria="tester", activo=True)
    ok = repo.delete(session, db_obj)

    assert ok is True
    assert db_obj.activo is False                 # borrado lógico
    session.add.assert_called_once_with(db_obj)
    session.delete.assert_not_called()
    session.commit.assert_called_once()


# ---------------------------
# Servicio: update / list_paginated (mock de repo)
# ---------------------------

def test_cargo_service_update_not_found_devuelve_none_y_no_actualiza():
    repo = MagicMock()
    repo.get.return_value = None

    service = CargoService()
    service.repo = repo

    out = service.update(MagicMock(), item_id=uuid4(), data={"nombre": "X"})
    assert out is None
    repo.update.assert_not_called()


def test_cargo_service_update_found_llama_repo_update():
    repo = MagicMock()
    repo.get.return_value = Cargo(nombre="A", usuario_auditoria="tester")  # objeto existente
    repo.update.return_value = "UPDATED"

    service = CargoService()
    service.repo = repo

    out = service.update(MagicMock(), item_id=uuid4(), data={"nombre": "B"})
    assert out == "UPDATED"
    repo.update.assert_called_once()


def test_cargo_service_list_paginated_retorna_items_y_meta():
    repo = MagicMock()
    repo.list.return_value = (["r1", "r2"], 10)

    service = CargoService()
    service.repo = repo

    items, meta = service.list_paginated(MagicMock(), limit=2, offset=4, only_active=True)

    assert items == ["r1", "r2"]
    assert meta.total == 10
    assert meta.limit == 2
    assert meta.offset == 4
    # dependiendo del total, has_more podría ser True o False; con 10 y offset 4 + limit 2 => True
    assert meta.has_more is True


# ---------------------------
# Verifica que update use model_dump(exclude_unset=True) cuando recibe Pydantic
# (es decir, que no sobreescriba con None campos no enviados)
# ---------------------------

def test_cargo_repository_update_no_sobrescribe_campos_no_enviados():
    from unittest.mock import MagicMock
    from src.osiris.modules.common.cargo.repository import CargoRepository
    from src.osiris.modules.common.cargo.entity import Cargo
    from src.osiris.modules.common.cargo.models import CargoUpdate

    session = MagicMock()
    repo = CargoRepository()

    # Estado inicial en DB
    db_obj = Cargo(nombre="Original", usuario_auditoria="tester")

    # DTO que NO envía 'nombre' -> debe mantenerse
    partial = CargoUpdate(usuario_auditoria="nueva")

    updated = repo.update(session, db_obj, partial)

    # Comportamiento esperado: solo cambia 'usuario_auditoria'
    assert updated.nombre == "Original"
    assert updated.usuario_auditoria == "nueva"

    # Persistencia llamada
    session.add.assert_called_once_with(db_obj)
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(db_obj)