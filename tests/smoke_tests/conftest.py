from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from osiris.core.db import get_session
from osiris.main import app
from osiris.modules.common.audit_log.entity import AuditLog
from osiris.modules.common.empresa.entity import Empresa
from osiris.modules.common.punto_emision.entity import PuntoEmision, PuntoEmisionSecuencial
from osiris.modules.common.sucursal.entity import Sucursal
from osiris.modules.facturacion.core_sri.models import (
    CuentaPorCobrar,
    DocumentoElectronico,
    DocumentoElectronicoHistorial,
    DocumentoSriCola,
    PagoCxC,
    Venta,
    VentaDetalle,
    VentaDetalleImpuesto,
)
from osiris.modules.inventario.bodega.entity import Bodega
from osiris.modules.inventario.casa_comercial.entity import CasaComercial
from osiris.modules.inventario.categoria.entity import Categoria
from osiris.modules.facturacion.inventario.models import (
    InventarioStock,
    MovimientoInventario,
    MovimientoInventarioDetalle,
)
from osiris.modules.inventario.producto.entity import (
    Producto,
    ProductoCategoria,
    ProductoImpuesto,
)
from osiris.modules.sri.impuesto_catalogo.entity import AplicaA, ImpuestoCatalogo, TipoImpuesto
from osiris.modules.sri.tipo_contribuyente.entity import TipoContribuyente


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(
        engine,
        tables=[
            TipoContribuyente.__table__,
            AuditLog.__table__,
            Empresa.__table__,
            Sucursal.__table__,
            PuntoEmision.__table__,
            PuntoEmisionSecuencial.__table__,
            Bodega.__table__,
            Categoria.__table__,
            CasaComercial.__table__,
            ImpuestoCatalogo.__table__,
            Producto.__table__,
            ProductoCategoria.__table__,
            ProductoImpuesto.__table__,
            MovimientoInventario.__table__,
            MovimientoInventarioDetalle.__table__,
            InventarioStock.__table__,
            Venta.__table__,
            VentaDetalle.__table__,
            VentaDetalleImpuesto.__table__,
            CuentaPorCobrar.__table__,
            PagoCxC.__table__,
            DocumentoElectronico.__table__,
            DocumentoElectronicoHistorial.__table__,
            DocumentoSriCola.__table__,
        ],
    )
    with Session(engine) as session:
        existe_tipo = session.get(TipoContribuyente, "01")
        if existe_tipo is None:
            session.add(
                TipoContribuyente(
                    codigo="01",
                    nombre="Sociedad",
                    activo=True,
                    usuario_auditoria="smoke",
                )
            )
            session.commit()

        iva = session.exec(
            select(ImpuestoCatalogo).where(
                ImpuestoCatalogo.tipo_impuesto == TipoImpuesto.IVA,
                ImpuestoCatalogo.codigo_sri == "2",
                ImpuestoCatalogo.activo.is_(True),
            )
        ).first()
        if iva is None:
            session.add(
                ImpuestoCatalogo(
                    tipo_impuesto=TipoImpuesto.IVA,
                    codigo_tipo_impuesto="2",
                    codigo_sri="2",
                    descripcion="IVA 0%",
                    vigente_desde=date.today(),
                    aplica_a=AplicaA.AMBOS,
                    porcentaje_iva=Decimal("0.00"),
                    usuario_auditoria="smoke",
                    activo=True,
                )
            )
            session.commit()
    return engine


@pytest.fixture(scope="session")
def client(test_engine):
    def override_get_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    app.state.security_audit_engine = test_engine
    with TestClient(app, base_url="http://testserver/api") as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def db_session(test_engine):
    with Session(test_engine) as session:
        yield session
