from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from pydantic import ValidationError
from sqlmodel import Session, select

from osiris.modules.facturacion.entity import (
    RetencionRecibida,
    RetencionRecibidaDetalle,
    Venta,
)
from osiris.modules.facturacion.models import (
    RetencionRecibidaCreate,
    RetencionRecibidaDetalleRead,
    RetencionRecibidaRead,
    q2,
)


class RetencionRecibidaService:
    def _validar_venta(self, session: Session, venta_id: UUID) -> Venta:
        venta = session.get(Venta, venta_id)
        if not venta or not venta.activo:
            raise HTTPException(status_code=404, detail="Venta no encontrada para registrar retencion recibida.")
        return venta

    def _validar_unicidad(self, session: Session, cliente_id: UUID, numero_retencion: str) -> None:
        existente = session.exec(
            select(RetencionRecibida).where(
                RetencionRecibida.cliente_id == cliente_id,
                RetencionRecibida.numero_retencion == numero_retencion,
                RetencionRecibida.activo.is_(True),
            )
        ).first()
        if existente:
            raise HTTPException(
                status_code=400,
                detail="Ya existe una retencion recibida con ese numero para el cliente.",
            )

    def crear_retencion_recibida(
        self,
        session: Session,
        payload: RetencionRecibidaCreate,
    ) -> RetencionRecibidaRead:
        venta = self._validar_venta(session, payload.venta_id)
        self._validar_unicidad(session, payload.cliente_id, payload.numero_retencion)
        subtotal_general = q2(
            venta.subtotal_12 + venta.subtotal_15 + venta.subtotal_0 + venta.subtotal_no_objeto
        )
        try:
            payload = RetencionRecibidaCreate.model_validate(
                payload.model_dump(),
                context={
                    "venta_subtotal_general": subtotal_general,
                    "venta_monto_iva": q2(venta.monto_iva),
                },
            )
        except ValidationError as exc:
            first_error = exc.errors()[0]["msg"] if exc.errors() else str(exc)
            raise HTTPException(status_code=400, detail=first_error) from exc

        retencion = RetencionRecibida(
            venta_id=payload.venta_id,
            cliente_id=payload.cliente_id,
            numero_retencion=payload.numero_retencion,
            clave_acceso_sri=payload.clave_acceso_sri,
            fecha_emision=payload.fecha_emision,
            estado=payload.estado,
            total_retenido=payload.total_retenido,
            usuario_auditoria=payload.usuario_auditoria,
            activo=True,
        )
        session.add(retencion)
        session.flush()

        for detalle in payload.detalles:
            session.add(
                RetencionRecibidaDetalle(
                    retencion_recibida_id=retencion.id,
                    codigo_impuesto_sri=detalle.codigo_impuesto_sri,
                    porcentaje_aplicado=detalle.porcentaje_aplicado,
                    base_imponible=detalle.base_imponible,
                    valor_retenido=detalle.valor_retenido,
                    usuario_auditoria=payload.usuario_auditoria,
                    activo=True,
                )
            )

        session.commit()
        return self.obtener_retencion_recibida_read(session, retencion.id)

    def obtener_retencion_recibida_read(
        self,
        session: Session,
        retencion_recibida_id: UUID,
    ) -> RetencionRecibidaRead:
        retencion = session.get(RetencionRecibida, retencion_recibida_id)
        if not retencion or not retencion.activo:
            raise HTTPException(status_code=404, detail="Retencion recibida no encontrada")

        detalles = list(
            session.exec(
                select(RetencionRecibidaDetalle).where(
                    RetencionRecibidaDetalle.retencion_recibida_id == retencion.id,
                    RetencionRecibidaDetalle.activo.is_(True),
                )
            ).all()
        )

        return RetencionRecibidaRead(
            id=retencion.id,
            venta_id=retencion.venta_id,
            cliente_id=retencion.cliente_id,
            numero_retencion=retencion.numero_retencion,
            clave_acceso_sri=retencion.clave_acceso_sri,
            fecha_emision=retencion.fecha_emision,
            estado=retencion.estado,
            total_retenido=retencion.total_retenido,
            detalles=[
                RetencionRecibidaDetalleRead.model_validate(detalle, from_attributes=True)
                for detalle in detalles
            ],
        )
