from __future__ import annotations

from pydantic import BaseModel, Field


class FEProcesarColaRead(BaseModel):
    procesados: int = Field(ge=0)
