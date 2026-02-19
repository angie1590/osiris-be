from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from osiris.modules.facturacion.models import (
    CompraCreate,
    ImpuestoAplicadoInput,
    VentaCompraDetalleCreate,
    VentaCreate,
)


def _iva12() -> ImpuestoAplicadoInput:
    return ImpuestoAplicadoInput(
        tipo_impuesto="IVA",
        codigo_impuesto_sri="2",
        codigo_porcentaje_sri="2",
        tarifa=Decimal("12"),
    )


def _iva15() -> ImpuestoAplicadoInput:
    return ImpuestoAplicadoInput(
        tipo_impuesto="IVA",
        codigo_impuesto_sri="2",
        codigo_porcentaje_sri="4",
        tarifa=Decimal("15"),
    )


def _iva0() -> ImpuestoAplicadoInput:
    return ImpuestoAplicadoInput(
        tipo_impuesto="IVA",
        codigo_impuesto_sri="2",
        codigo_porcentaje_sri="0",
        tarifa=Decimal("0"),
    )


def _ice5() -> ImpuestoAplicadoInput:
    return ImpuestoAplicadoInput(
        tipo_impuesto="ICE",
        codigo_impuesto_sri="3",
        codigo_porcentaje_sri="305",
        tarifa=Decimal("5"),
    )


def test_venta_create_calcula_totales_e_impuestos_al_centavo():
    venta = VentaCreate(
        tipo_identificacion_comprador="RUC",
        identificacion_comprador="1790012345001",
        forma_pago="EFECTIVO",
        usuario_auditoria="tester",
        detalles=[
            VentaCompraDetalleCreate(
                producto_id=uuid4(),
                descripcion="A",
                cantidad=Decimal("2"),
                precio_unitario=Decimal("10"),
                impuestos=[_iva12()],
            ),
            VentaCompraDetalleCreate(
                producto_id=uuid4(),
                descripcion="B",
                cantidad=Decimal("1"),
                precio_unitario=Decimal("100"),
                descuento=Decimal("10"),
                impuestos=[_iva15(), _ice5()],
            ),
            VentaCompraDetalleCreate(
                producto_id=uuid4(),
                descripcion="C",
                cantidad=Decimal("1"),
                precio_unitario=Decimal("50"),
                impuestos=[_iva0()],
            ),
            VentaCompraDetalleCreate(
                producto_id=uuid4(),
                descripcion="D",
                cantidad=Decimal("1"),
                precio_unitario=Decimal("30"),
                impuestos=[],
            ),
        ],
    )

    assert venta.subtotal_sin_impuestos == Decimal("190.00")
    assert venta.subtotal_12 == Decimal("20.00")
    assert venta.subtotal_15 == Decimal("90.00")
    assert venta.subtotal_0 == Decimal("50.00")
    assert venta.subtotal_no_objeto == Decimal("30.00")
    assert venta.monto_iva == Decimal("15.90")
    assert venta.monto_ice == Decimal("4.50")
    assert venta.valor_total == Decimal("210.40")


def test_compra_create_calcula_totales_redondeados():
    compra = CompraCreate(
        tipo_identificacion_proveedor="RUC",
        identificacion_proveedor="1790099988001",
        forma_pago="TRANSFERENCIA",
        usuario_auditoria="tester",
        detalles=[
            VentaCompraDetalleCreate(
                producto_id=uuid4(),
                descripcion="INSUMO",
                cantidad=Decimal("3"),
                precio_unitario=Decimal("0.99"),
                impuestos=[_iva12()],
            ),
            VentaCompraDetalleCreate(
                producto_id=uuid4(),
                descripcion="SERVICIO",
                cantidad=Decimal("1"),
                precio_unitario=Decimal("10"),
                impuestos=[],
            ),
        ],
    )

    # base1 = 2.97, iva = 0.3564 -> 0.36
    assert compra.subtotal_sin_impuestos == Decimal("12.97")
    assert compra.subtotal_12 == Decimal("2.97")
    assert compra.subtotal_no_objeto == Decimal("10.00")
    assert compra.monto_iva == Decimal("0.36")
    assert compra.monto_ice == Decimal("0.00")
    assert compra.valor_total == Decimal("13.33")
