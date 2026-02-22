from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from osiris.modules.common.audit_log.entity import AuditLog
from osiris.modules.common.empresa.entity import Empresa
from osiris.modules.common.sucursal.entity import Sucursal
from osiris.modules.facturacion.compras.services.compra_service import CompraService
from osiris.modules.facturacion.core_sri.models import (
    Compra,
    CompraDetalle,
    CompraDetalleImpuesto,
    CuentaPorPagar,
    EstadoCuentaPorPagar,
    TipoImpuestoMVP,
)
from osiris.modules.facturacion.core_sri.all_schemas import (
    CompraCreate,
    CompraUpdate,
    ImpuestoAplicadoInput,
    VentaCompraDetalleCreate,
)
from osiris.modules.inventario.bodega.entity import Bodega
from osiris.modules.inventario.casa_comercial.entity import CasaComercial
from osiris.modules.facturacion.inventario.models import (
    EstadoMovimientoInventario,
    InventarioStock,
    MovimientoInventario,
    MovimientoInventarioDetalle,
    TipoMovimientoInventario,
)
from osiris.modules.inventario.producto.entity import Producto, TipoProducto
from osiris.modules.sri.tipo_contribuyente.entity import TipoContribuyente


def _build_test_engine():
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
            Compra.__table__,
            CompraDetalle.__table__,
            CompraDetalleImpuesto.__table__,
            CuentaPorPagar.__table__,
            MovimientoInventario.__table__,
            MovimientoInventarioDetalle.__table__,
            InventarioStock.__table__,
            AuditLog.__table__,
        ],
    )
    return engine


def test_compra_genera_ingreso_inventario():
    engine = _build_test_engine()
    service = CompraService()

    with Session(engine) as session:
        tipo = TipoContribuyente(codigo="01", nombre="Sociedad", activo=True)
        session.add(tipo)

        empresa = Empresa(
            razon_social="Empresa Compras",
            nombre_comercial="Empresa Compras",
            ruc="1790012345001",
            direccion_matriz="Av. Central",
            telefono="022345678",
            obligado_contabilidad=True,
            regimen="GENERAL",
            modo_emision="ELECTRONICO",
            tipo_contribuyente_id="01",
            usuario_auditoria="seed",
            activo=True,
        )
        session.add(empresa)
        session.flush()

        bodega = Bodega(
            codigo_bodega="BOD-CMP-001",
            nombre_bodega="Bodega Compras",
            empresa_id=empresa.id,
            usuario_auditoria="seed",
            activo=True,
        )
        session.add(bodega)

        producto = Producto(
            nombre="Producto Compra Orq",
            tipo=TipoProducto.BIEN,
            pvp=Decimal("10.00"),
            cantidad=0,
            usuario_auditoria="seed",
            activo=True,
        )
        session.add(producto)
        session.flush()

        stock = InventarioStock(
            bodega_id=bodega.id,
            producto_id=producto.id,
            cantidad_actual=Decimal("10.0000"),
            costo_promedio_vigente=Decimal("10.0000"),
            usuario_auditoria="seed",
            activo=True,
        )
        session.add(stock)
        session.commit()

        compra = service.registrar_compra(
            session,
            CompraCreate(
                proveedor_id=empresa.id,
                secuencial_factura="001-001-123456789",
                autorizacion_sri="1" * 49,
                fecha_emision=date.today(),
                bodega_id=bodega.id,
                sustento_tributario="01",
                tipo_identificacion_proveedor="RUC",
                identificacion_proveedor="1790099988001",
                forma_pago="TRANSFERENCIA",
                usuario_auditoria="compras.user",
                detalles=[
                    VentaCompraDetalleCreate(
                        producto_id=producto.id,
                        descripcion="Ingreso compra",
                        cantidad=Decimal("10.0000"),
                        precio_unitario=Decimal("20.0000"),
                        descuento=Decimal("0.00"),
                        impuestos=[
                            ImpuestoAplicadoInput(
                                tipo_impuesto=TipoImpuestoMVP.IVA,
                                codigo_impuesto_sri="2",
                                codigo_porcentaje_sri="0",
                                tarifa=Decimal("0.00"),
                            )
                        ],
                    )
                ],
            ),
        )

        movimiento = session.exec(
            select(MovimientoInventario).where(
                MovimientoInventario.referencia_documento == f"COMPRA:{compra.id}",
                MovimientoInventario.tipo_movimiento == TipoMovimientoInventario.INGRESO,
            )
        ).first()
        assert movimiento is not None
        assert movimiento.estado == EstadoMovimientoInventario.CONFIRMADO

        stock_actual = session.exec(
            select(InventarioStock).where(
                InventarioStock.bodega_id == bodega.id,
                InventarioStock.producto_id == producto.id,
            )
        ).one()
        assert stock_actual.cantidad_actual == Decimal("20.0000")
        assert stock_actual.costo_promedio_vigente == Decimal("15.0000")


def test_compra_registrada_no_permite_edicion():
    engine = _build_test_engine()
    service = CompraService()

    with Session(engine) as session:
        tipo = TipoContribuyente(codigo="01", nombre="Sociedad", activo=True)
        session.add(tipo)
        empresa = Empresa(
            razon_social="Empresa Compras Edit",
            nombre_comercial="Empresa Compras Edit",
            ruc="1790012345001",
            direccion_matriz="Av. Central",
            telefono="022345678",
            obligado_contabilidad=True,
            regimen="GENERAL",
            modo_emision="ELECTRONICO",
            tipo_contribuyente_id="01",
            usuario_auditoria="seed",
            activo=True,
        )
        session.add(empresa)
        session.flush()
        bodega = Bodega(
            codigo_bodega="BOD-CMP-002",
            nombre_bodega="Bodega Compras Edit",
            empresa_id=empresa.id,
            usuario_auditoria="seed",
            activo=True,
        )
        session.add(bodega)
        producto = Producto(
            nombre="Producto Compra Edit",
            tipo=TipoProducto.BIEN,
            pvp=Decimal("10.00"),
            cantidad=0,
            usuario_auditoria="seed",
            activo=True,
        )
        session.add(producto)
        session.commit()

        compra = service.registrar_compra(
            session,
            CompraCreate(
                proveedor_id=empresa.id,
                secuencial_factura="001-001-999999999",
                autorizacion_sri="3" * 49,
                fecha_emision=date.today(),
                bodega_id=bodega.id,
                sustento_tributario="01",
                tipo_identificacion_proveedor="RUC",
                identificacion_proveedor="1790099988001",
                forma_pago="EFECTIVO",
                usuario_auditoria="compras.user",
                detalles=[
                    VentaCompraDetalleCreate(
                        producto_id=producto.id,
                        descripcion="Ingreso compra",
                        cantidad=Decimal("1.0000"),
                        precio_unitario=Decimal("5.0000"),
                        descuento=Decimal("0.00"),
                        impuestos=[],
                    )
                ],
            ),
        )

        with pytest.raises(HTTPException) as exc:
            service.actualizar_compra(
                session,
                compra.id,
                CompraUpdate(
                    secuencial_factura="001-001-111111111",
                    usuario_auditoria="edit.user",
                ),
            )

        assert exc.value.status_code == 400
        assert "no se puede editar una compra en estado registrada" in exc.value.detail.lower()


def test_registro_compra_inicializa_cxp():
    engine = _build_test_engine()
    service = CompraService()

    with Session(engine) as session:
        tipo = TipoContribuyente(codigo="01", nombre="Sociedad", activo=True)
        session.add(tipo)
        empresa = Empresa(
            razon_social="Empresa CxP",
            nombre_comercial="Empresa CxP",
            ruc="1790012345001",
            direccion_matriz="Av. Central",
            telefono="022345678",
            obligado_contabilidad=True,
            regimen="GENERAL",
            modo_emision="ELECTRONICO",
            tipo_contribuyente_id="01",
            usuario_auditoria="seed",
            activo=True,
        )
        session.add(empresa)
        session.flush()
        bodega = Bodega(
            codigo_bodega="BOD-CXP-001",
            nombre_bodega="Bodega CxP",
            empresa_id=empresa.id,
            usuario_auditoria="seed",
            activo=True,
        )
        session.add(bodega)
        producto = Producto(
            nombre="Producto CxP",
            tipo=TipoProducto.BIEN,
            pvp=Decimal("10.00"),
            cantidad=0,
            usuario_auditoria="seed",
            activo=True,
        )
        session.add(producto)
        session.commit()

        compra = service.registrar_compra(
            session,
            CompraCreate(
                proveedor_id=empresa.id,
                secuencial_factura="001-001-222222222",
                autorizacion_sri="4" * 49,
                fecha_emision=date.today(),
                bodega_id=bodega.id,
                sustento_tributario="01",
                tipo_identificacion_proveedor="RUC",
                identificacion_proveedor="1790099988001",
                forma_pago="EFECTIVO",
                usuario_auditoria="compras.user",
                detalles=[
                    VentaCompraDetalleCreate(
                        producto_id=producto.id,
                        descripcion="Compra base CxP",
                        cantidad=Decimal("10.0000"),
                        precio_unitario=Decimal("10.0000"),
                        descuento=Decimal("0.00"),
                        impuestos=[],
                    )
                ],
            ),
        )

        cxp = session.exec(
            select(CuentaPorPagar).where(CuentaPorPagar.compra_id == compra.id)
        ).first()
        assert cxp is not None
        assert cxp.valor_total_factura == Decimal("100.00")
        assert cxp.valor_retenido == Decimal("0.00")
        assert cxp.pagos_acumulados == Decimal("0.00")
        assert cxp.saldo_pendiente == Decimal("100.00")
        assert cxp.estado == EstadoCuentaPorPagar.PENDIENTE
