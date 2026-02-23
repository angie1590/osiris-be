from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from osiris.core.db import get_session
from osiris.main import app
from osiris.modules.common.audit_log.entity import AuditLog
from osiris.modules.inventario.atributo.entity import Atributo, TipoDato
from osiris.modules.inventario.casa_comercial.entity import CasaComercial
from osiris.modules.inventario.producto.entity import Producto, TipoProducto
from osiris.modules.inventario.producto.models_atributos import (
    ProductoAtributoValor,
    ProductoAtributoValorUpsert,
)
from osiris.modules.inventario.producto.service_atributos import ProductoAtributoValorService


def _build_test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(
        engine,
        tables=[
            AuditLog.__table__,
            CasaComercial.__table__,
            Producto.__table__,
            Atributo.__table__,
            ProductoAtributoValor.__table__,
        ],
    )
    return engine


def _seed_producto_y_atributo(session: Session, tipo_dato: TipoDato) -> tuple[Producto, Atributo]:
    producto = Producto(
        nombre=f"Producto-{uuid4().hex[:8]}",
        tipo=TipoProducto.BIEN,
        pvp=Decimal("10.00"),
        usuario_auditoria="tester",
        activo=True,
    )
    atributo = Atributo(
        nombre=f"Atributo-{uuid4().hex[:8]}",
        tipo_dato=tipo_dato,
        usuario_auditoria="tester",
        activo=True,
    )
    session.add(producto)
    session.add(atributo)
    session.commit()
    session.refresh(producto)
    session.refresh(atributo)
    return producto, atributo


def test_upsert_valores_producto_rechaza_tipo_invalido_integer():
    engine = _build_test_engine()
    service = ProductoAtributoValorService()

    with Session(engine) as session:
        producto, atributo_integer = _seed_producto_y_atributo(session, TipoDato.INTEGER)

        with pytest.raises(HTTPException) as exc:
            service.upsert_valores_producto(
                session,
                producto.id,
                [ProductoAtributoValorUpsert(atributo_id=atributo_integer.id, valor="hola")],
            )

        assert exc.value.status_code == 400
        assert exc.value.detail == "El valor enviado no coincide con el tipo de dato del atributo"


def test_upsert_valores_producto_asigna_columna_sql_correcta():
    engine = _build_test_engine()
    service = ProductoAtributoValorService()

    with Session(engine) as session:
        producto, atributo_integer = _seed_producto_y_atributo(session, TipoDato.INTEGER)

        service.upsert_valores_producto(
            session,
            producto.id,
            [ProductoAtributoValorUpsert(atributo_id=atributo_integer.id, valor="123")],
        )

        row = session.exec(
            select(ProductoAtributoValor)
            .where(ProductoAtributoValor.producto_id == producto.id)
            .where(ProductoAtributoValor.atributo_id == atributo_integer.id)
        ).first()

        assert row is not None
        assert row.valor_integer == 123
        assert row.valor_string is None
        assert row.valor_decimal is None
        assert row.valor_boolean is None
        assert row.valor_date is None


def test_endpoint_upsert_producto_atributos_e2e_ok():
    engine = _build_test_engine()

    with Session(engine) as session:
        producto, atributo_integer = _seed_producto_y_atributo(session, TipoDato.INTEGER)
        producto_id = str(producto.id)
        atributo_id = str(atributo_integer.id)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/productos/{producto_id}/atributos",
                json=[{"atributo_id": atributo_id, "valor": "77"}],
            )
            assert response.status_code == 200
            body = response.json()
            assert isinstance(body, list)
            assert body[0]["atributo_id"] == atributo_id
            assert body[0]["valor_integer"] == 77
    finally:
        app.dependency_overrides.pop(get_session, None)
