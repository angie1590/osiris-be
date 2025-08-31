# src/core/settings.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic import Field, ValidationError, field_validator, AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import dotenv_values


BASE_DIR = Path(__file__).resolve().parents[2]  # .../src
PROJECT_ROOT = BASE_DIR.parent                  # repo root

class Settings(BaseSettings):
    # === Entorno ===
    ENVIRONMENT: str = Field(default="development", description="development|staging|production")

    # === Firma electrónica / fe-ec ===
    FEEC_P12_PATH: Path
    FEEC_P12_PASSWORD: str
    FEEC_XSD_PATH: Path
    FEEC_AMBIENTE: str = Field(default="pruebas")  # pruebas | produccion

    # === DB (compose) ===
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # === URLs DB ===
    DATABASE_URL: AnyUrl  # para app (sqlmodel / runtime)
    DB_URL_ALEMBIC: Optional[AnyUrl] = None  # para alembic.ini si se necesita distinto

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    # --- Validaciones y normalización ---
    @field_validator("FEEC_AMBIENTE")
    @classmethod
    def _check_ambiente(cls, v: str) -> str:
        if v not in {"pruebas", "produccion"}:
            raise ValueError("FEEC_AMBIENTE debe ser 'pruebas' o 'produccion'")
        return v

    @field_validator("FEEC_P12_PATH", "FEEC_XSD_PATH")
    @classmethod
    def _file_exists(cls, v: Path, info):
        # Permite rutas relativas al root del proyecto
        v = v if v.is_absolute() else (PROJECT_ROOT / v).resolve()
        if not v.exists():
            raise ValueError(f"Archivo no encontrado en `{info.field_name}`: {v}")
        return v

def load_settings() -> Settings:
    env_name = os.getenv("ENVIRONMENT", "development")
    env_file = PROJECT_ROOT / f".env.{env_name}"
    # Carga explícita de .env.<ENV> + override por entorno real
    base = dotenv_values(env_file) if env_file.exists() else {}
    try:
        return Settings(**base)  # BaseSettings aún toma del os.environ
    except ValidationError as e:
        lines = [f"Error de configuración ({env_file.name}):"]
        for err in e.errors():
            loc = ".".join(str(x) for x in err["loc"])
            lines.append(f" - {loc}: {err['msg']}")
        raise RuntimeError("\n".join(lines))

settings = load_settings()
