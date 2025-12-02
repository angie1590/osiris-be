# src/osiris/modules/inventario/categoria_atributo/service.py
from __future__ import annotations

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlmodel import select

from osiris.modules.inventario.categoria_atributo.entity import CategoriaAtributo
from .models import CategoriaAtributoCreate, CategoriaAtributoUpdate

class CategoriaAtributoService:
    def list_paginated(self, session: Session, skip: int = 0, limit: int = 50, categoria_id: Optional[UUID] = None) -> list[CategoriaAtributo]:
        query = select(CategoriaAtributo).where(CategoriaAtributo.activo == True)
        if categoria_id:
            query = query.where(CategoriaAtributo.categoria_id == categoria_id)
        query = query.offset(skip).limit(limit)
        return list(session.exec(query))

    def get(self, session: Session, id: UUID) -> Optional[CategoriaAtributo]:
        return session.get(CategoriaAtributo, id)

    def create(self, session: Session, dto: CategoriaAtributoCreate, usuario_auditoria: Optional[str] = None) -> CategoriaAtributo:
        entity = CategoriaAtributo(
            categoria_id=dto.categoria_id,
            atributo_id=dto.atributo_id,
            orden=dto.orden,
            obligatorio=dto.obligatorio,
            usuario_auditoria=usuario_auditoria or "api",
            activo=True,
        )
        session.add(entity)
        session.commit()
        session.refresh(entity)
        return entity

    def update(self, session: Session, id: UUID, dto: CategoriaAtributoUpdate, usuario_auditoria: Optional[str] = None) -> Optional[CategoriaAtributo]:
        entity = session.get(CategoriaAtributo, id)
        if not entity:
            return None
        if dto.orden is not None:
            entity.orden = dto.orden
        if dto.obligatorio is not None:
            entity.obligatorio = dto.obligatorio
        entity.usuario_auditoria = usuario_auditoria or entity.usuario_auditoria
        session.add(entity)
        session.commit()
        session.refresh(entity)
        return entity

    def delete(self, session: Session, id: UUID, usuario_auditoria: Optional[str] = None) -> bool:
        entity = session.get(CategoriaAtributo, id)
        if not entity:
            return False
        entity.activo = False
        entity.usuario_auditoria = usuario_auditoria or entity.usuario_auditoria
        session.add(entity)
        session.commit()
        return True
