# src/osiris/modules/inventario/bodega/service.py
from __future__ import annotations

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlmodel import select

from osiris.modules.inventario.bodega.entity import Bodega
from .models import BodegaCreate, BodegaUpdate


class BodegaService:
    def list_paginated(
        self,
        session: Session,
        skip: int = 0,
        limit: int = 50,
        empresa_id: Optional[UUID] = None,
        sucursal_id: Optional[UUID] = None,
    ) -> list[Bodega]:
        query = select(Bodega).where(Bodega.activo.is_(True))
        if empresa_id:
            query = query.where(Bodega.empresa_id == empresa_id)
        if sucursal_id:
            query = query.where(Bodega.sucursal_id == sucursal_id)
        query = query.offset(skip).limit(limit)
        return list(session.exec(query))

    def get(self, session: Session, id: UUID) -> Optional[Bodega]:
        return session.get(Bodega, id)

    def create(
        self,
        session: Session,
        dto: BodegaCreate,
        usuario_auditoria: Optional[str] = None,
    ) -> Bodega:
        entity = Bodega(
            codigo_bodega=dto.codigo_bodega,
            nombre_bodega=dto.nombre_bodega,
            descripcion=dto.descripcion,
            empresa_id=dto.empresa_id,
            sucursal_id=dto.sucursal_id,
            usuario_auditoria=usuario_auditoria or "api",
            activo=True,
        )
        session.add(entity)
        session.commit()
        session.refresh(entity)
        return entity

    def update(
        self,
        session: Session,
        id: UUID,
        dto: BodegaUpdate,
        usuario_auditoria: Optional[str] = None,
    ) -> Optional[Bodega]:
        entity = session.get(Bodega, id)
        if not entity:
            return None
        if dto.codigo_bodega is not None:
            entity.codigo_bodega = dto.codigo_bodega
        if dto.nombre_bodega is not None:
            entity.nombre_bodega = dto.nombre_bodega
        if dto.descripcion is not None:
            entity.descripcion = dto.descripcion
        if dto.sucursal_id is not None:
            entity.sucursal_id = dto.sucursal_id
        entity.usuario_auditoria = usuario_auditoria or entity.usuario_auditoria
        session.add(entity)
        session.commit()
        session.refresh(entity)
        return entity

    def delete(
        self,
        session: Session,
        id: UUID,
        usuario_auditoria: Optional[str] = None,
    ) -> bool:
        entity = session.get(Bodega, id)
        if not entity:
            return False
        entity.activo = False
        entity.usuario_auditoria = usuario_auditoria or entity.usuario_auditoria
        session.add(entity)
        session.commit()
        return True
