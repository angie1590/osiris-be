from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from osiris.modules.facturacion.entity import (
    Compra,
    PlantillaRetencion,
    PlantillaRetencionDetalle,
    TipoRetencionSRI,
)
from osiris.modules.facturacion.models import (
    GuardarPlantillaRetencionRequest,
    PlantillaRetencionDetalleRead,
    PlantillaRetencionRead,
    RetencionSugeridaDetalleRead,
    RetencionSugeridaRead,
    q2,
)


class RetencionService:
    def _obtener_compra(self, session: Session, compra_id: UUID) -> Compra:
        compra = session.get(Compra, compra_id)
        if not compra or not compra.activo:
            raise HTTPException(status_code=404, detail="Compra no encontrada")
        return compra

    def _obtener_plantilla_para_proveedor(
        self,
        session: Session,
        proveedor_id: UUID,
    ) -> PlantillaRetencion | None:
        stmt = (
            select(PlantillaRetencion)
            .where(
                PlantillaRetencion.activo.is_(True),
                PlantillaRetencion.proveedor_id == proveedor_id,
            )
            .order_by(PlantillaRetencion.actualizado_en.desc())
        )
        plantilla = session.exec(stmt).first()
        if plantilla:
            return plantilla

        stmt_global = (
            select(PlantillaRetencion)
            .where(
                PlantillaRetencion.activo.is_(True),
                PlantillaRetencion.es_global.is_(True),
            )
            .order_by(PlantillaRetencion.actualizado_en.desc())
        )
        return session.exec(stmt_global).first()

    def _obtener_detalles_plantilla(
        self,
        session: Session,
        plantilla_id: UUID,
    ) -> list[PlantillaRetencionDetalle]:
        stmt = (
            select(PlantillaRetencionDetalle)
            .where(
                PlantillaRetencionDetalle.activo.is_(True),
                PlantillaRetencionDetalle.plantilla_retencion_id == plantilla_id,
            )
            .order_by(PlantillaRetencionDetalle.creado_en.asc())
        )
        return list(session.exec(stmt).all())

    def sugerir_retencion(self, session: Session, compra_id: UUID) -> RetencionSugeridaRead:
        compra = self._obtener_compra(session, compra_id)
        plantilla = self._obtener_plantilla_para_proveedor(session, compra.proveedor_id)
        if not plantilla:
            raise HTTPException(
                status_code=404,
                detail="No existe plantilla de retencion para el proveedor ni plantilla global.",
            )

        detalles_plantilla = self._obtener_detalles_plantilla(session, plantilla.id)
        if not detalles_plantilla:
            raise HTTPException(status_code=400, detail="La plantilla de retencion no tiene detalles.")

        sugeridos: list[RetencionSugeridaDetalleRead] = []
        total_retenido = Decimal("0.00")
        for detalle in detalles_plantilla:
            base = q2(compra.monto_iva) if detalle.tipo == TipoRetencionSRI.IVA else q2(compra.subtotal_sin_impuestos)
            valor = q2(base * q2(detalle.porcentaje) / Decimal("100"))
            sugeridos.append(
                RetencionSugeridaDetalleRead(
                    codigo_retencion_sri=detalle.codigo_retencion_sri,
                    tipo=detalle.tipo,
                    porcentaje=q2(detalle.porcentaje),
                    base_calculo=base,
                    valor_retenido=valor,
                )
            )
            total_retenido += valor

        return RetencionSugeridaRead(
            compra_id=compra.id,
            plantilla_id=plantilla.id,
            proveedor_id=plantilla.proveedor_id,
            detalles=sugeridos,
            total_retenido=q2(total_retenido),
        )

    def guardar_plantilla_desde_retencion_digitada(
        self,
        session: Session,
        compra_id: UUID,
        payload: GuardarPlantillaRetencionRequest,
    ) -> PlantillaRetencionRead:
        compra = self._obtener_compra(session, compra_id)
        proveedor_id = None if payload.es_global else compra.proveedor_id

        if not payload.es_global:
            prev_stmt = select(PlantillaRetencion).where(
                PlantillaRetencion.activo.is_(True),
                PlantillaRetencion.proveedor_id == compra.proveedor_id,
            )
        else:
            prev_stmt = select(PlantillaRetencion).where(
                PlantillaRetencion.activo.is_(True),
                PlantillaRetencion.es_global.is_(True),
            )
        previas = list(session.exec(prev_stmt).all())
        for previa in previas:
            previa.activo = False
            previa.usuario_auditoria = payload.usuario_auditoria
            session.add(previa)

        plantilla = PlantillaRetencion(
            proveedor_id=proveedor_id,
            nombre=payload.nombre,
            es_global=payload.es_global,
            usuario_auditoria=payload.usuario_auditoria,
            activo=True,
        )
        session.add(plantilla)
        session.flush()

        for detalle in payload.detalles:
            session.add(
                PlantillaRetencionDetalle(
                    plantilla_retencion_id=plantilla.id,
                    codigo_retencion_sri=detalle.codigo_retencion_sri,
                    tipo=detalle.tipo,
                    porcentaje=q2(detalle.porcentaje),
                    usuario_auditoria=payload.usuario_auditoria,
                    activo=True,
                )
            )

        session.commit()
        return self.obtener_plantilla_read(session, plantilla.id)

    def obtener_plantilla_read(self, session: Session, plantilla_id: UUID) -> PlantillaRetencionRead:
        plantilla = session.get(PlantillaRetencion, plantilla_id)
        if not plantilla or not plantilla.activo:
            raise HTTPException(status_code=404, detail="Plantilla de retencion no encontrada")
        detalles = self._obtener_detalles_plantilla(session, plantilla.id)
        return PlantillaRetencionRead(
            id=plantilla.id,
            proveedor_id=plantilla.proveedor_id,
            nombre=plantilla.nombre,
            es_global=plantilla.es_global,
            detalles=[
                PlantillaRetencionDetalleRead.model_validate(detalle, from_attributes=True)
                for detalle in detalles
            ],
        )
