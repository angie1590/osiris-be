from __future__ import annotations

from typing import Optional
from uuid import UUID
from fastapi import HTTPException
from sqlmodel import Session, select

from osiris.domain.service import BaseService
from .repository import PuntoEmisionRepository
from .entity import PuntoEmision, PuntoEmisionSecuencial, TipoDocumentoSRI
from osiris.modules.common.empresa.entity import Empresa
from osiris.modules.common.rol.entity import Rol
from osiris.modules.common.sucursal.entity import Sucursal
from osiris.modules.common.usuario.entity import Usuario


class PuntoEmisionService(BaseService):
    repo = PuntoEmisionRepository()
    fk_models = {
        "empresa_id": Empresa,
        "sucursal_id": Sucursal,
    }

    # ---------- atajos ----------
    def list_by_empresa_sucursal(
        self, session: Session, *, empresa_id: UUID, sucursal_id: Optional[UUID],
        limit: int, offset: int, only_active: bool = True
    ):
        kwargs = {"empresa_id": empresa_id}
        if sucursal_id is not None:
            kwargs["sucursal_id"] = sucursal_id
        return self.list_paginated(session, limit=limit, offset=offset, only_active=only_active, **kwargs)

    def get_by_clave_natural(
        self, session: Session, *, empresa_id: UUID, codigo: str,
        sucursal_id: Optional[UUID] = None, only_active: Optional[bool] = None
    ) -> Optional[PuntoEmision]:
        stmt = select(PuntoEmision).where(
            PuntoEmision.empresa_id == empresa_id,
            PuntoEmision.codigo == codigo,
        )
        if sucursal_id is not None:
            stmt = stmt.where(PuntoEmision.sucursal_id == sucursal_id)
        if only_active is True:
            stmt = stmt.where(PuntoEmision.activo.is_(True))
        return session.exec(stmt).first()

    @staticmethod
    def _require_admin(session: Session, usuario_id: UUID) -> None:
        stmt = (
            select(Usuario, Rol)
            .join(Rol, Rol.id == Usuario.rol_id)
            .where(
                Usuario.id == usuario_id,
                Usuario.activo.is_(True),
                Rol.activo.is_(True),
            )
        )
        row = session.exec(stmt).first()
        if not row:
            raise HTTPException(status_code=403, detail="Usuario administrador invalido o inactivo")

        _, rol = row
        if rol.nombre.strip().upper() not in {"ADMIN", "ADMINISTRADOR"}:
            raise HTTPException(status_code=403, detail="Solo un administrador puede ajustar secuenciales")

    def obtener_siguiente_secuencial(
        self,
        session: Session,
        *,
        punto_emision_id: UUID,
        tipo_documento: TipoDocumentoSRI,
        usuario_auditoria: Optional[str] = None,
    ) -> int:
        return self.repo.obtener_siguiente_secuencial(
            session,
            punto_emision_id=punto_emision_id,
            tipo_documento=tipo_documento,
            usuario_auditoria=usuario_auditoria,
        )

    def ajustar_secuencial_manual(
        self,
        session: Session,
        *,
        punto_emision_id: UUID,
        tipo_documento: TipoDocumentoSRI,
        nuevo_secuencial: int,
        usuario_id: UUID,
        justificacion: str,
    ) -> PuntoEmisionSecuencial:
        if not justificacion or not justificacion.strip():
            raise HTTPException(status_code=400, detail="La justificacion es obligatoria")

        self._require_admin(session, usuario_id)
        return self.repo.ajustar_secuencial_manual(
            session,
            punto_emision_id=punto_emision_id,
            tipo_documento=tipo_documento,
            nuevo_secuencial=nuevo_secuencial,
            usuario_id=usuario_id,
            justificacion=justificacion.strip(),
        )
