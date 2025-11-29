"""
Tests unitarios para ProductoImpuesto (repository, service, asignación)
"""
import pytest
from datetime import date, timedelta
from uuid import uuid4
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from osiris.modules.inventario.producto.entity import Producto, TipoProducto
from osiris.modules.aux.impuesto_catalogo.entity import (
    ImpuestoCatalogo,
    TipoImpuesto,
    ClasificacionIVA,
    AplicaA
)
from osiris.modules.inventario.producto.entity import ProductoImpuesto
from osiris.modules.inventario.producto_impuesto.models import ProductoImpuestoCreate
from osiris.modules.inventario.producto_impuesto.repository import ProductoImpuestoRepository
from osiris.modules.inventario.producto_impuesto.service import ProductoImpuestoService


# ==================== REPOSITORY TESTS ====================

def test_repo_validar_maximo_por_tipo_cuando_ya_existe():
    """Debe lanzar HTTPException cuando ya existe 1 impuesto del mismo tipo"""
    repo = ProductoImpuestoRepository()
    session = MagicMock()

    producto_id = uuid4()

    # Mock count_by_tipo_impuesto para que devuelva 1
    repo.count_by_tipo_impuesto = MagicMock(return_value=1)

    with pytest.raises(HTTPException) as exc_info:
        repo.validar_maximo_por_tipo(session, producto_id, TipoImpuesto.IVA)
    assert exc_info.value.status_code == 400
    assert "máximo" in exc_info.value.detail.lower()


def test_repo_validar_maximo_por_tipo_cuando_no_existe():
    """No debe lanzar excepción cuando no hay impuestos del tipo"""
    repo = ProductoImpuestoRepository()
    session = MagicMock()

    producto_id = uuid4()

    # Mock count_by_tipo_impuesto para que devuelva 0
    repo.count_by_tipo_impuesto = MagicMock(return_value=0)

    # No debe lanzar excepción
    repo.validar_maximo_por_tipo(session, producto_id, TipoImpuesto.IVA)


def test_repo_validar_duplicado_cuando_existe():
    """Debe lanzar HTTPException cuando ya existe la combinación producto-impuesto"""
    repo = ProductoImpuestoRepository()
    session = MagicMock()

    producto_id = uuid4()
    impuesto_id = uuid4()

    # Mock get_by_producto_impuesto para que devuelva un registro
    repo.get_by_producto_impuesto = MagicMock(return_value=ProductoImpuesto(
        id=uuid4(),
        producto_id=producto_id,
        impuesto_catalogo_id=impuesto_id,
        activo=True,
        usuario_auditoria="test_user"
    ))

    with pytest.raises(HTTPException) as exc_info:
        repo.validar_duplicado(session, producto_id, impuesto_id)
    assert exc_info.value.status_code == 409


# ==================== SERVICE TESTS ====================

def test_service_asignar_impuesto_producto_no_existe():
    """No se puede asignar impuesto a producto inexistente"""
    service = ProductoImpuestoService()
    session = MagicMock()

    producto_id = uuid4()
    impuesto_id = uuid4()

    # Mock session.get para que devuelva None (producto no existe)
    session.get.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        service.asignar_impuesto(session, producto_id, impuesto_id, "test_user")
    assert exc_info.value.status_code == 404


def test_service_asignar_impuesto_producto_inactivo_falla():
    """No se puede asignar impuesto a producto inactivo"""
    service = ProductoImpuestoService()
    session = MagicMock()

    producto_id = uuid4()
    impuesto_id = uuid4()

    producto_inactivo = Producto(
        id=producto_id,
        nombre="Producto Test",
        tipo=TipoProducto.BIEN,
        pvp=100.0,
        activo=False,  # INACTIVO
        usuario_auditoria="test_user"
    )

    # Mock session.get para devolver producto inactivo
    session.get.return_value = producto_inactivo

    with pytest.raises(HTTPException) as exc_info:
        service.asignar_impuesto(session, producto_id, impuesto_id, "test_user")
    assert exc_info.value.status_code == 404
    assert "inactivo" in exc_info.value.detail.lower()


def test_service_validar_compatibilidad_tipo_bien_con_impuesto_solo_servicio():
    """Producto BIEN no puede tener impuesto solo para SERVICIO"""
    service = ProductoImpuestoService()

    with pytest.raises(HTTPException) as exc_info:
        service._validar_compatibilidad_tipo(TipoProducto.BIEN, AplicaA.SERVICIO)
    assert exc_info.value.status_code == 400
    assert "no aplica" in exc_info.value.detail.lower()


def test_service_validar_compatibilidad_tipo_bien_con_impuesto_ambos():
    """Producto BIEN puede tener impuesto para AMBOS"""
    service = ProductoImpuestoService()

    # No debe lanzar excepción
    service._validar_compatibilidad_tipo(TipoProducto.BIEN, AplicaA.AMBOS)


def test_service_validar_compatibilidad_tipo_servicio_con_impuesto_solo_bien():
    """Producto SERVICIO no puede tener impuesto solo para BIEN"""
    service = ProductoImpuestoService()

    with pytest.raises(HTTPException) as exc_info:
        service._validar_compatibilidad_tipo(TipoProducto.SERVICIO, AplicaA.BIEN)
    assert exc_info.value.status_code == 400
    assert "no aplica" in exc_info.value.detail.lower()
