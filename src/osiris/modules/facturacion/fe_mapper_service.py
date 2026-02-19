from __future__ import annotations

from decimal import Decimal

from osiris.modules.facturacion.entity import FormaPagoSRI, TipoIdentificacionSRI
from osiris.modules.facturacion.models import VentaRead, q2


FORMA_PAGO_SRI_CODE = {
    FormaPagoSRI.EFECTIVO: "01",
    FormaPagoSRI.TARJETA: "19",
    FormaPagoSRI.TRANSFERENCIA: "20",
}

IDENTIFICACION_SRI_CODE = {
    TipoIdentificacionSRI.RUC: "04",
    TipoIdentificacionSRI.CEDULA: "05",
    TipoIdentificacionSRI.PASAPORTE: "06",
}


def _fmt(value: Decimal) -> str:
    return f"{q2(value):.2f}"


class FEMapperService:
    def venta_to_fe_payload(self, venta: VentaRead) -> dict:
        total_con_impuestos: dict[tuple[str, str], dict[str, Decimal]] = {}
        detalles_payload: list[dict] = []

        for detalle in venta.detalles:
            impuestos_payload = []
            for impuesto in detalle.impuestos:
                key = (impuesto.codigo_impuesto_sri, impuesto.codigo_porcentaje_sri)
                if key not in total_con_impuestos:
                    total_con_impuestos[key] = {"base": Decimal("0.00"), "valor": Decimal("0.00")}
                total_con_impuestos[key]["base"] += impuesto.base_imponible
                total_con_impuestos[key]["valor"] += impuesto.valor_impuesto

                impuestos_payload.append(
                    {
                        "codigo": impuesto.codigo_impuesto_sri,
                        "codigoPorcentaje": impuesto.codigo_porcentaje_sri,
                        "tarifa": _fmt(impuesto.tarifa),
                        "baseImponible": _fmt(impuesto.base_imponible),
                        "valor": _fmt(impuesto.valor_impuesto),
                    }
                )

            detalles_payload.append(
                {
                    "descripcion": detalle.descripcion,
                    "cantidad": _fmt(detalle.cantidad),
                    "precioUnitario": _fmt(detalle.precio_unitario),
                    "descuento": _fmt(detalle.descuento),
                    "precioTotalSinImpuesto": _fmt(detalle.subtotal_sin_impuesto),
                    "impuestos": impuestos_payload,
                }
            )

        total_con_impuestos_list = [
            {
                "codigo": codigo,
                "codigoPorcentaje": codigo_porcentaje,
                "baseImponible": _fmt(data["base"]),
                "valor": _fmt(data["valor"]),
            }
            for (codigo, codigo_porcentaje), data in total_con_impuestos.items()
        ]

        return {
            "infoTributaria": {
                "identificacionComprador": venta.identificacion_comprador,
                "tipoIdentificacionComprador": IDENTIFICACION_SRI_CODE[venta.tipo_identificacion_comprador],
            },
            "infoFactura": {
                "fechaEmision": venta.fecha_emision.isoformat(),
                "totalSinImpuestos": _fmt(venta.subtotal_sin_impuestos),
                "totalConImpuestos": total_con_impuestos_list,
                "importeTotal": _fmt(venta.valor_total),
                "pagos": [
                    {
                        "formaPago": FORMA_PAGO_SRI_CODE[venta.forma_pago],
                        "total": _fmt(venta.valor_total),
                    }
                ],
            },
            "detalles": detalles_payload,
        }
