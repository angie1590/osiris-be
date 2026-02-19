from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from osiris.modules.common.audit_log.entity import AuditLog
from osiris.modules.common.empresa.entity import Empresa
from osiris.modules.common.sucursal.entity import Sucursal
from osiris.modules.inventario.bodega.entity import Bodega
from osiris.modules.inventario.casa_comercial.entity import CasaComercial
from osiris.modules.inventario.movimiento_inventario.entity import (
    EstadoMovimientoInventario,
    MovimientoInventario,
    MovimientoInventarioDetalle,
    TipoMovimientoInventario,
)
from osiris.modules.inventario.movimiento_inventario.models import MovimientoInventarioCreate
from osiris.modules.inventario.movimiento_inventario.service import MovimientoInventarioService
from osiris.modules.inventario.producto.entity import Producto
from osiris.modules.sri.tipo_contribuyente.entity import TipoContribuyente


def _build_test_engine():
    # Algunos tests unitarios limpian SQLModel.metadata durante la colección.
    # Re-registramos tablas requeridas para resolver FKs por nombre.
    for table in (
        TipoContribuyente.__table__,
        Empresa.__table__,
        Sucursal.__table__,
        Bodega.__table__,
        CasaComercial.__table__,
        Producto.__table__,
        AuditLog.__table__,
        MovimientoInventario.__table__,
        MovimientoInventarioDetalle.__table__,
    ):
        if table.key not in SQLModel.metadata.tables:
            SQLModel.metadata._add_table(table.name, table.schema, table)  # type: ignore[attr-defined]

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(
        engine,
        tables=[
            TipoContribuyente.__table__,
            Empresa.__table__,
            Sucursal.__table__,
            Bodega.__table__,
            CasaComercial.__table__,
            Producto.__table__,
            AuditLog.__table__,
            # Tablas nuevas
            MovimientoInventario.__table__,
            MovimientoInventarioDetalle.__table__,
        ],
    )
    return engine


def test_crear_movimiento_borrador():
    engine = _build_test_engine()
    service = MovimientoInventarioService()

    with Session(engine) as session:
        tipo_contribuyente = TipoContribuyente(codigo="01", nombre="SOCIEDAD", activo=True)
        session.add(tipo_contribuyente)

        empresa = Empresa(
            razon_social="Empresa Inventario",
            nombre_comercial="Empresa Inventario",
            ruc="1790012345001",
            direccion_matriz="Av. Quito",
            telefono="022345678",
            obligado_contabilidad=True,
            regimen="GENERAL",
            modo_emision="ELECTRONICO",
            tipo_contribuyente_id="01",
            usuario_auditoria="tester",
            activo=True,
        )
        session.add(empresa)
        session.flush()

        bodega = Bodega(
            codigo_bodega="BOD-001",
            nombre_bodega="Bodega Principal",
            empresa_id=empresa.id,
            usuario_auditoria="tester",
            activo=True,
        )
        session.add(bodega)

        producto = Producto(
            nombre="Producto Kardex",
            tipo="BIEN",
            pvp=Decimal("10.00"),
            cantidad=25,
            usuario_auditoria="tester",
            activo=True,
        )
        session.add(producto)
        session.commit()
        session.refresh(bodega)
        session.refresh(producto)

        payload = MovimientoInventarioCreate(
            bodega_id=bodega.id,
            tipo_movimiento=TipoMovimientoInventario.EGRESO,
            referencia_documento="FAC-00001",
            usuario_auditoria="tester",
            detalles=[
                {
                    "producto_id": producto.id,
                    "cantidad": Decimal("2.00"),
                    "costo_unitario": Decimal("5.25"),
                }
            ],
        )

        movimiento = service.crear_movimiento_borrador(session, payload)
        session.refresh(producto)

        detalles = session.exec(
            select(MovimientoInventarioDetalle).where(
                MovimientoInventarioDetalle.movimiento_inventario_id == movimiento.id
            )
        ).all()

        assert movimiento.estado == EstadoMovimientoInventario.BORRADOR
        assert len(detalles) == 1
        assert detalles[0].cantidad == Decimal("2.00")
        # Criterio E3-1: crear BORRADOR no altera stock.
        assert producto.cantidad == 25


@pytest.mark.parametrize("cantidad", [Decimal("0"), Decimal("-1")])
def test_validacion_cantidades_negativas(cantidad: Decimal):
    with pytest.raises(ValidationError):
        MovimientoInventarioCreate(
            bodega_id="11111111-1111-1111-1111-111111111111",
            tipo_movimiento=TipoMovimientoInventario.INGRESO,
            referencia_documento="DOC-TEST",
            detalles=[
                {
                    "producto_id": "22222222-2222-2222-2222-222222222222",
                    "cantidad": cantidad,
                    "costo_unitario": Decimal("1.00"),
                }
            ],
        )
