# src/osiris/modules/inventario/categoria_atributo/service.py
from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlmodel import select

from osiris.modules.inventario.atributo.entity import Atributo, TipoDato
from osiris.modules.inventario.categoria_atributo.entity import CategoriaAtributo
from .models import CategoriaAtributoCreate, CategoriaAtributoUpdate


class CategoriaAtributoService:
    @staticmethod
    def _is_empty_default(value: Optional[str]) -> bool:
        return value is None or (isinstance(value, str) and value.strip() == "")

    @staticmethod
    def _build_safe_default(tipo_dato: Optional[TipoDato]) -> Optional[str]:
        if tipo_dato is None:
            return None
        if tipo_dato == TipoDato.STRING:
            return "N/A"
        if tipo_dato == TipoDato.INTEGER:
            return "0"
        if tipo_dato == TipoDato.DECIMAL:
            return "0.00"
        if tipo_dato == TipoDato.BOOLEAN:
            return "false"
        if tipo_dato == TipoDato.DATE:
            return date.today().isoformat()
        return None

    def list_paginated(self, session: Session, skip: int = 0, limit: int = 50, categoria_id: Optional[UUID] = None) -> list[CategoriaAtributo]:
        query = select(CategoriaAtributo).where(CategoriaAtributo.activo.is_(True))
        if categoria_id:
            query = query.where(CategoriaAtributo.categoria_id == categoria_id)
        query = query.offset(skip).limit(limit)
        return list(session.exec(query))

    def get(self, session: Session, id: UUID) -> Optional[CategoriaAtributo]:
        return session.get(CategoriaAtributo, id)

    def create(self, session: Session, dto: CategoriaAtributoCreate, usuario_auditoria: Optional[str] = None) -> CategoriaAtributo:
        valor_default = dto.valor_default
        if dto.obligatorio is True and self._is_empty_default(valor_default):
            atributo = session.get(Atributo, dto.atributo_id)
            valor_default = self._build_safe_default(getattr(atributo, "tipo_dato", None))

        entity = CategoriaAtributo(
            categoria_id=dto.categoria_id,
            atributo_id=dto.atributo_id,
            orden=dto.orden,
            obligatorio=dto.obligatorio,
            valor_default=valor_default,
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

        if dto.valor_default is not None:
            valor_default = dto.valor_default
        else:
            valor_default = entity.valor_default

        if dto.obligatorio is True and self._is_empty_default(valor_default):
            atributo = session.get(Atributo, entity.atributo_id)
            valor_default = self._build_safe_default(getattr(atributo, "tipo_dato", None))

        if dto.valor_default is not None or dto.obligatorio is True:
            entity.valor_default = valor_default

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
