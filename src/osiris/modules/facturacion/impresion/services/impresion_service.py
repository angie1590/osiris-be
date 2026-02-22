from __future__ import annotations

import base64
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session

from osiris.core.settings import get_settings
from osiris.modules.common.empresa.entity import Empresa
from osiris.modules.facturacion.core_sri.models import (
    DocumentoElectronico,
    EstadoDocumentoElectronico,
    TipoDocumentoElectronico,
    Venta,
)
from osiris.modules.facturacion.impresion.strategies.render_strategy import RenderStrategy
from osiris.modules.facturacion.impresion.strategies.ride_a4_strategy import RideA4Strategy


class ImpresionService:
    def __init__(self, strategy: RenderStrategy | None = None) -> None:
        self.strategy = strategy or RideA4Strategy()
        self.templates_dir = Path(__file__).resolve().parents[1] / "templates"

    @staticmethod
    def _barcode_data_uri(clave_acceso: str) -> str:
        try:
            from io import BytesIO

            import barcode  # type: ignore
            from barcode.writer import SVGWriter  # type: ignore

            output = BytesIO()
            code128 = barcode.get("code128", clave_acceso, writer=SVGWriter())
            code128.write(output)
            svg_bytes = output.getvalue()
        except ModuleNotFoundError:
            svg = (
                "<svg xmlns='http://www.w3.org/2000/svg' width='560' height='65'>"
                "<rect width='100%' height='100%' fill='white'/>"
                "<text x='8' y='35' font-size='14' fill='black'>"
                f"{clave_acceso}"
                "</text>"
                "</svg>"
            )
            svg_bytes = svg.encode("utf-8")

        encoded = base64.b64encode(svg_bytes).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"

    def _render_html(self, context: dict) -> str:
        template_path = self.templates_dir / "ride_a4.html"
        if not template_path.exists():
            raise HTTPException(status_code=500, detail="Plantilla RIDE A4 no encontrada.")

        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape  # type: ignore

            env = Environment(
                loader=FileSystemLoader(str(self.templates_dir)),
                autoescape=select_autoescape(["html", "xml"]),
            )
            template = env.get_template("ride_a4.html")
            return template.render(**context)
        except ModuleNotFoundError:
            # Fallback para entornos sin Jinja2 instalado.
            template = template_path.read_text(encoding="utf-8")
            html = template
            html = html.replace("{{ razon_social }}", str(context["razon_social"]))
            html = html.replace("{{ ruc }}", str(context["ruc"]))
            html = html.replace("{{ clave_acceso }}", str(context["clave_acceso"]))
            html = html.replace("{{ ambiente }}", str(context["ambiente"]))
            html = html.replace("{{ fecha_emision }}", str(context["fecha_emision"]))
            html = html.replace("{{ subtotal }}", str(context["subtotal"]))
            html = html.replace("{{ iva_total }}", str(context["iva_total"]))
            html = html.replace("{{ total }}", str(context["total"]))
            html = html.replace("{{ barcode_data_uri }}", str(context["barcode_data_uri"]))
            html = html.replace("{{ logo_url }}", str(context["logo_url"]))
            return html

    def _payload_from_documento(self, session: Session, documento: DocumentoElectronico) -> dict:
        venta = None
        if documento.tipo_documento == TipoDocumentoElectronico.FACTURA:
            venta_id = documento.referencia_id or documento.venta_id
            if venta_id is not None:
                venta = session.get(Venta, venta_id)

        empresa = session.get(Empresa, venta.empresa_id) if venta and venta.empresa_id else None
        settings = get_settings()
        ambiente = "Pruebas" if settings.FEEC_AMBIENTE.lower() == "pruebas" else "Produccion"

        subtotal = "0.00"
        iva_total = "0.00"
        total = "0.00"
        fecha_emision = ""
        if venta is not None:
            subtotal = str(venta.subtotal_sin_impuestos)
            iva_total = str(venta.monto_iva)
            total = str(venta.valor_total)
            fecha_emision = venta.fecha_emision.isoformat()

        clave = documento.clave_acceso or "SIN_CLAVE_ACCESO"
        return {
            "logo_url": empresa.logo if empresa and empresa.logo else "",
            "razon_social": empresa.razon_social if empresa else "RAZON SOCIAL",
            "ruc": empresa.ruc if empresa else "RUC_NO_DISPONIBLE",
            "clave_acceso": clave,
            "ambiente": ambiente,
            "subtotal": subtotal,
            "iva_total": iva_total,
            "total": total,
            "fecha_emision": fecha_emision,
            "barcode_data_uri": self._barcode_data_uri(clave),
        }

    def generar_ride_a4(self, session: Session, *, documento_id: UUID) -> bytes:
        documento = session.get(DocumentoElectronico, documento_id)
        if not documento or not documento.activo:
            raise HTTPException(status_code=404, detail="Documento electrónico no encontrado.")
        if documento.estado_sri != EstadoDocumentoElectronico.AUTORIZADO:
            raise HTTPException(status_code=400, detail="Solo se puede imprimir RIDE de documentos AUTORIZADOS.")

        payload = self._payload_from_documento(session, documento)
        html = self._render_html(payload)
        return self.strategy.render_pdf(html)

