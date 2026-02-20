from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from osiris.modules.common.audit_log.entity import AuditLog
from osiris.modules.common.empresa.entity import Empresa
from osiris.modules.common.sucursal.entity import Sucursal
from osiris.modules.facturacion.entity import (
    CuentaPorCobrar,
    EstadoCuentaPorCobrar,
    EstadoVenta,
    FormaPagoSRI,
    TipoIdentificacionSRI,
    Venta,
    VentaDetalle,
)
from osiris.modules.facturacion.models import q2
from osiris.modules.facturacion.venta_service import VentaService
from osiris.modules.inventario.bodega.entity import Bodega
from osiris.modules.inventario.casa_comercial.entity import CasaComercial
from osiris.modules.inventario.movimiento_inventario.entity import (
    InventarioStock,
    MovimientoInventario,
    MovimientoInventarioDetalle,
)
from osiris.modules.inventario.movimiento_inventario.service import MovimientoInventarioService
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
            Venta.__table__,
            VentaDetalle.__table__,
            MovimientoInventario.__table__,
            MovimientoInventarioDetalle.__table__,
            InventarioStock.__table__,
            CuentaPorCobrar.__table__,
            AuditLog.__table__,
        ],
    )
    return engine


def _seed_data(session: Session, *, stock_inicial: Decimal, cantidad_venta: Decimal) -> tuple[Venta, Bodega, Producto]:
    tipo = TipoContribuyente(codigo="01", nombre="Sociedad", activo=True)
    session.add(tipo)

    empresa = Empresa(
        razon_social="Empresa Emision Venta",
        nombre_comercial="Empresa Emision Venta",
        ruc="1790012345001",
        direccion_matriz="Av. Principal",
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
        codigo_bodega="BOD-E6-001",
        nombre_bodega="Bodega E6",
        empresa_id=empresa.id,
        usuario_auditoria="seed",
        activo=True,
    )
    session.add(bodega)

    producto = Producto(
        nombre=f"Producto E6 {stock_inicial}",
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
        cantidad_actual=stock_inicial,
        costo_promedio_vigente=Decimal("5.0000"),
        usuario_auditoria="seed",
        activo=True,
    )
    session.add(stock)

    subtotal = q2(cantidad_venta * Decimal("10.00"))
    venta = Venta(
        fecha_emision=date.today(),
        tipo_identificacion_comprador=TipoIdentificacionSRI.RUC,
        identificacion_comprador="1790012345001",
        forma_pago=FormaPagoSRI.EFECTIVO,
        subtotal_sin_impuestos=subtotal,
        subtotal_12=Decimal("0.00"),
        subtotal_15=Decimal("0.00"),
        subtotal_0=subtotal,
        subtotal_no_objeto=Decimal("0.00"),
        monto_iva=Decimal("0.00"),
        monto_ice=Decimal("0.00"),
        valor_total=subtotal,
        estado=EstadoVenta.BORRADOR,
        usuario_auditoria="seed",
        activo=True,
    )
    session.add(venta)
    session.flush()

    session.add(
        VentaDetalle(
            venta_id=venta.id,
            producto_id=producto.id,
            descripcion="Detalle venta E6",
            cantidad=cantidad_venta,
            precio_unitario=Decimal("10.0000"),
            descuento=Decimal("0.00"),
            subtotal_sin_impuesto=subtotal,
            usuario_auditoria="seed",
            activo=True,
        )
    )
    session.commit()
    session.refresh(venta)
    return venta, bodega, producto


def test_emitir_venta_bloqueo_sin_stock():
    engine = _build_test_engine()
    service = VentaService()

    with Session(engine) as session:
        venta, _, _ = _seed_data(
            session,
            stock_inicial=Decimal("2.0000"),
            cantidad_venta=Decimal("5.0000"),
        )

        with pytest.raises(ValueError) as exc:
            service.emitir_venta(
                session,
                venta.id,
                usuario_auditoria="tester",
            )

        assert "Stock insuficiente para el producto" in str(exc.value)
        session.refresh(venta)
        assert venta.estado == EstadoVenta.BORRADOR

        cxc = session.exec(
            select(CuentaPorCobrar).where(CuentaPorCobrar.venta_id == venta.id)
        ).one_or_none()
        assert cxc is None


def test_emitir_venta_flujo_exitoso():
    engine = _build_test_engine()
    service = VentaService()
    kardex_service = MovimientoInventarioService()

    with Session(engine) as session:
        venta, bodega, producto = _seed_data(
            session,
            stock_inicial=Decimal("15.0000"),
            cantidad_venta=Decimal("5.0000"),
        )

        emitted = service.emitir_venta(
            session,
            venta.id,
            usuario_auditoria="tester",
        )

        assert emitted.estado == EstadoVenta.EMITIDA

        stock = session.exec(
            select(InventarioStock).where(
                InventarioStock.bodega_id == bodega.id,
                InventarioStock.producto_id == producto.id,
            )
        ).one()
        assert stock.cantidad_actual == Decimal("10.0000")

        kardex = kardex_service.obtener_kardex(
            session,
            producto_id=producto.id,
            bodega_id=bodega.id,
        )
        assert kardex["movimientos"][-1]["cantidad_salida"] == Decimal("5.0000")

        cxc = session.exec(
            select(CuentaPorCobrar).where(CuentaPorCobrar.venta_id == venta.id)
        ).one_or_none()
        assert cxc is not None
        assert cxc.estado == EstadoCuentaPorCobrar.PENDIENTE
        assert cxc.saldo_pendiente == Decimal("50.00")
