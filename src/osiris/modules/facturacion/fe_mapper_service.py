from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session

from osiris.modules.common.empresa.entity import RegimenTributario
from osiris.modules.facturacion.entity import (
    DocumentoElectronico,
    DocumentoElectronicoHistorial,
    EstadoDocumentoElectronico,
    FormaPagoSRI,
    TipoIdentificacionSRI,
    TipoImpuestoMVP,
)
from osiris.modules.facturacion.models import RetencionRead, VentaRead, q2


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


def _totales_impuestos_desde_detalle(venta: VentaRead) -> tuple[Decimal, Decimal, Decimal]:
    total = Decimal("0.00")
    total_iva = Decimal("0.00")
    total_ice = Decimal("0.00")

    for detalle in venta.detalles:
        for impuesto in detalle.impuestos:
            valor = q2(impuesto.valor_impuesto)
            total += valor
            if impuesto.tipo_impuesto == TipoImpuestoMVP.IVA:
                total_iva += valor
            elif impuesto.tipo_impuesto == TipoImpuestoMVP.ICE:
                total_ice += valor

    return q2(total), q2(total_iva), q2(total_ice)


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

        total_detalle_impuestos, total_detalle_iva, total_detalle_ice = _totales_impuestos_desde_detalle(venta)
        if total_detalle_iva != q2(venta.monto_iva):
            raise ValueError(
                "Inconsistencia tributaria: el IVA de detalle no coincide con la cabecera de la venta."
            )
        if total_detalle_ice != q2(venta.monto_ice):
            raise ValueError(
                "Inconsistencia tributaria: el ICE de detalle no coincide con la cabecera de la venta."
            )
        if total_detalle_impuestos != q2(venta.monto_iva + venta.monto_ice):
            raise ValueError(
                "Inconsistencia tributaria: la suma de impuestos en detalle no coincide con la cabecera."
            )

        total_con_impuestos_list = [
            {
                "codigo": codigo,
                "codigoPorcentaje": codigo_porcentaje,
                "baseImponible": _fmt(data["base"]),
                "valor": _fmt(data["valor"]),
            }
            for (codigo, codigo_porcentaje), data in sorted(total_con_impuestos.items())
        ]
        total_agrupado = q2(sum((data["valor"] for data in total_con_impuestos.values()), Decimal("0.00")))
        if total_agrupado != total_detalle_impuestos:
            raise ValueError(
                "Inconsistencia tributaria: totalConImpuestos no cuadra con los impuestos de detalle."
            )

        if q2(venta.subtotal_sin_impuestos + total_detalle_impuestos) != q2(venta.valor_total):
            raise ValueError(
                "Inconsistencia tributaria: subtotal mas impuestos no coincide con el valor total."
            )

        payload = {
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
        if venta.regimen_emisor == RegimenTributario.RIMPE_NEGOCIO_POPULAR:
            payload["infoAdicional"] = {
                "campoAdicional": [
                    {
                        "nombre": "Contribuyente",
                        "valor": "Contribuyente Negocio Popular - Régimen RIMPE",
                    }
                ]
            }
        return payload

    def retencion_to_fe_payload(self, retencion: RetencionRead) -> dict:
        impuestos = [
            {
                "codigoRetencion": detalle.codigo_retencion_sri,
                "tipo": detalle.tipo.value if hasattr(detalle.tipo, "value") else str(detalle.tipo),
                "baseImponible": _fmt(detalle.base_calculo),
                "porcentajeRetener": _fmt(detalle.porcentaje),
                "valorRetenido": _fmt(detalle.valor_retenido),
            }
            for detalle in retencion.detalles
        ]

        total = q2(sum((detalle.valor_retenido for detalle in retencion.detalles), Decimal("0.00")))
        if total != q2(retencion.total_retenido):
            raise ValueError("Inconsistencia tributaria: el total retenido no cuadra con los detalles.")

        return {
            "retencion": {
                "compraId": str(retencion.compra_id),
                "fechaEmision": retencion.fecha_emision.isoformat(),
                "estado": retencion.estado.value if hasattr(retencion.estado, "value") else str(retencion.estado),
                "totalRetenido": _fmt(retencion.total_retenido),
                "impuestos": impuestos,
            }
        }

    def registrar_respuesta_sri(
        self,
        session: Session,
        documento_electronico_id: UUID,
        estado_nuevo: EstadoDocumentoElectronico | str,
        *,
        mensaje_sri: str,
        usuario_id: str | None = None,
    ) -> DocumentoElectronico:
        documento = session.get(DocumentoElectronico, documento_electronico_id)
        if not documento or not documento.activo:
            raise HTTPException(status_code=404, detail="Documento electronico no encontrado")

        destino = (
            estado_nuevo
            if isinstance(estado_nuevo, EstadoDocumentoElectronico)
            else EstadoDocumentoElectronico(estado_nuevo)
        )
        anterior = documento.estado.value if hasattr(documento.estado, "value") else str(documento.estado)
        motivo = (mensaje_sri or "").strip()

        if destino == EstadoDocumentoElectronico.RECHAZADO and not motivo:
            raise ValueError("motivo_cambio es obligatorio cuando el SRI rechaza el comprobante")
        if not motivo:
            motivo = f"Respuesta SRI: {destino.value}"

        documento.estado = destino
        session.add(documento)
        session.add(
            DocumentoElectronicoHistorial(
                entidad_id=documento.id,
                estado_anterior=anterior,
                estado_nuevo=destino.value,
                motivo_cambio=motivo,
                usuario_id=usuario_id,
            )
        )
        session.commit()
        session.refresh(documento)
        return documento
