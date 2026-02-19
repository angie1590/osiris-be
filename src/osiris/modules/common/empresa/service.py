from __future__ import annotations

from fastapi import HTTPException
from pydantic import ValidationError
from sqlmodel import Session

from osiris.modules.sri.tipo_contribuyente.entity import TipoContribuyente
from osiris.domain.service import BaseService
from .entity import ModoEmisionEmpresa, RegimenTributario
from .models import EmpresaRegimenModoRules
from .repository import EmpresaRepository


class EmpresaService(BaseService):
    fk_models = {
        "tipo_contribuyente_id": (TipoContribuyente, "codigo"),
    }
    repo = EmpresaRepository()

    def _validate_regimen_modo(self, regimen, modo_emision) -> None:
        try:
            EmpresaRegimenModoRules(
                regimen=regimen,
                modo_emision=modo_emision,
            )
        except ValidationError as exc:
            raise HTTPException(
                status_code=400,
                detail=exc.errors()[0]["msg"],
            ) from exc

    def validate_create(self, data, session: Session) -> None:
        regimen = data.get("regimen", RegimenTributario.GENERAL)
        modo_emision = data.get("modo_emision", ModoEmisionEmpresa.ELECTRONICO)
        self._validate_regimen_modo(regimen, modo_emision)

    def update(self, session: Session, item_id, data):
        db_obj = self.repo.get(session, item_id)
        if not db_obj:
            return None

        regimen = data.get("regimen", db_obj.regimen)
        modo_emision = data.get("modo_emision", db_obj.modo_emision)
        self._validate_regimen_modo(regimen, modo_emision)

        self._check_fk_active_and_exists(session, data)
        return self.repo.update(session, db_obj, data)
