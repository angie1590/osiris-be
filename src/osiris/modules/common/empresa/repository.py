from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from osiris.domain.repository import BaseRepository
from osiris.modules.common.audit_log.entity import AuditLog
from .entity import Empresa


class EmpresaRepository(BaseRepository):
    model = Empresa

    @staticmethod
    def _snapshot(model_obj: Empresa) -> dict:
        fields = model_obj.__class__.model_fields.keys()
        snapshot = {}
        for field in fields:
            value = getattr(model_obj, field)
            if isinstance(value, Enum):
                snapshot[field] = value.value
            elif isinstance(value, (datetime, UUID)):
                snapshot[field] = str(value)
            else:
                snapshot[field] = value
        return json.loads(json.dumps(snapshot, default=str))

    def update(self, session, db_obj, data):
        if isinstance(data, BaseModel):
            data = data.model_dump(exclude_unset=True)
        elif not isinstance(data, dict):
            raise ValueError("update() solo acepta dict o BaseModel como data")

        old_state = self._snapshot(db_obj)

        for field, value in data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        if hasattr(db_obj, "actualizado_en"):
            db_obj.actualizado_en = datetime.utcnow()

        new_state = self._snapshot(db_obj)

        audit = AuditLog(
            entidad="Empresa",
            entidad_id=db_obj.id,
            accion="UPDATE",
            estado_anterior=old_state,
            estado_nuevo=new_state,
            usuario_auditoria=data.get("usuario_auditoria", getattr(db_obj, "usuario_auditoria", None)),
        )

        session.add(db_obj)
        session.add(audit)
        try:
            session.commit()
        except Exception as e:
            from sqlalchemy.exc import IntegrityError

            session.rollback()
            if isinstance(e, IntegrityError):
                self._raise_integrity(e)
            raise
        session.refresh(db_obj)
        return db_obj
