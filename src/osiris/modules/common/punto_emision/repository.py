# src/osiris/modules/common/punto_emision/repository.py
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import select

from osiris.domain.repository import BaseRepository
from osiris.modules.common.audit_log.entity import AuditLog
from .entity import PuntoEmision, PuntoEmisionSecuencial, TipoDocumentoSRI

class PuntoEmisionRepository(BaseRepository):
    model = PuntoEmision

    def apply_filters(
        self,
        stmt,
        *,
        empresa_id: Optional[UUID] = None,
        sucursal_id: Optional[UUID] = None,
        only_active: Optional[bool] = None,
        **kw,
    ):
        if empresa_id:
            stmt = stmt.where(PuntoEmision.empresa_id == empresa_id)
        if sucursal_id:
            stmt = stmt.where(PuntoEmision.sucursal_id == sucursal_id)
        return stmt

    @staticmethod
    def _lock_punto_emision(session, punto_emision_id: UUID) -> PuntoEmision:
        stmt = (
            select(PuntoEmision)
            .where(
                PuntoEmision.id == punto_emision_id,
                PuntoEmision.activo.is_(True),
            )
            .with_for_update()
        )
        punto_emision = session.exec(stmt).first()
        if not punto_emision:
            raise HTTPException(status_code=404, detail="Punto de emision no encontrado o inactivo")
        return punto_emision

    @staticmethod
    def _lock_or_init_secuencial(
        session,
        *,
        punto_emision: PuntoEmision,
        tipo_documento: TipoDocumentoSRI,
    ) -> PuntoEmisionSecuencial:
        stmt = (
            select(PuntoEmisionSecuencial)
            .where(
                PuntoEmisionSecuencial.punto_emision_id == punto_emision.id,
                PuntoEmisionSecuencial.tipo_documento == tipo_documento,
            )
            .with_for_update()
        )
        secuencial = session.exec(stmt).first()
        if secuencial:
            if hasattr(secuencial, "activo") and secuencial.activo is False:
                secuencial.activo = True
            return secuencial

        initial = punto_emision.secuencial_actual if tipo_documento == TipoDocumentoSRI.FACTURA else 0
        secuencial = PuntoEmisionSecuencial(
            punto_emision_id=punto_emision.id,
            tipo_documento=tipo_documento,
            secuencial_actual=initial,
            usuario_auditoria=punto_emision.usuario_auditoria,
            activo=True,
        )
        session.add(secuencial)
        session.flush()
        return secuencial

    def obtener_siguiente_secuencial(
        self,
        session,
        *,
        punto_emision_id: UUID,
        tipo_documento: TipoDocumentoSRI,
        usuario_auditoria: Optional[str] = None,
    ) -> int:
        punto_emision = self._lock_punto_emision(session, punto_emision_id)
        secuencial = self._lock_or_init_secuencial(
            session,
            punto_emision=punto_emision,
            tipo_documento=tipo_documento,
        )

        secuencial.secuencial_actual += 1
        if hasattr(secuencial, "actualizado_en"):
            secuencial.actualizado_en = datetime.utcnow()
        if usuario_auditoria:
            secuencial.usuario_auditoria = usuario_auditoria

        session.add(secuencial)
        session.commit()
        session.refresh(secuencial)
        return secuencial.secuencial_actual

    def ajustar_secuencial_manual(
        self,
        session,
        *,
        punto_emision_id: UUID,
        tipo_documento: TipoDocumentoSRI,
        nuevo_secuencial: int,
        usuario_id: UUID,
        justificacion: str,
    ) -> PuntoEmisionSecuencial:
        punto_emision = self._lock_punto_emision(session, punto_emision_id)
        secuencial = self._lock_or_init_secuencial(
            session,
            punto_emision=punto_emision,
            tipo_documento=tipo_documento,
        )

        estado_anterior = {
            "punto_emision_id": str(punto_emision_id),
            "tipo_documento": tipo_documento.value,
            "secuencial_actual": secuencial.secuencial_actual,
        }
        secuencial.secuencial_actual = nuevo_secuencial
        secuencial.usuario_auditoria = str(usuario_id)
        if hasattr(secuencial, "actualizado_en"):
            secuencial.actualizado_en = datetime.utcnow()

        estado_nuevo = {
            "punto_emision_id": str(punto_emision_id),
            "tipo_documento": tipo_documento.value,
            "secuencial_actual": nuevo_secuencial,
            "justificacion": justificacion,
        }
        audit = AuditLog(
            entidad="PuntoEmisionSecuencial",
            entidad_id=secuencial.id,
            accion="MANUAL_ADJUST",
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            usuario_auditoria=str(usuario_id),
        )

        session.add(secuencial)
        session.add(audit)
        session.commit()
        session.refresh(secuencial)
        return secuencial
