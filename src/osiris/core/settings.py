from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values
from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]  # .../src
PROJECT_ROOT = BASE_DIR.parent  # repo root


class Settings(BaseSettings):
    # Entorno
    ENVIRONMENT: str = Field(
        default="development",
        description="development|staging|production",
    )

    # Facturacion electronica / FE-EC
    FEEC_P12_PATH: Path
    FEEC_P12_PASSWORD: str
    FEEC_XSD_PATH: Path
    FEEC_AMBIENTE: str = Field(default="pruebas")  # pruebas | produccion

    # DB
    DATABASE_URL: str
    DB_URL_ALEMBIC: str | None = None
    SQL_ECHO: bool = False

    # Parametros de compose (se mantienen para tener un solo settings de DB)
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    @field_validator("FEEC_AMBIENTE")
    @classmethod
    def _check_ambiente(cls, value: str) -> str:
        if value not in {"pruebas", "produccion"}:
            raise ValueError("FEEC_AMBIENTE debe ser 'pruebas' o 'produccion'")
        return value

    @field_validator("FEEC_P12_PATH", "FEEC_XSD_PATH")
    @classmethod
    def _file_exists(cls, value: Path, info):
        resolved_path = value if value.is_absolute() else (PROJECT_ROOT / value).resolve()
        if not resolved_path.exists():
            raise ValueError(f"Archivo no encontrado en `{info.field_name}`: {resolved_path}")
        return resolved_path

    @field_validator("DATABASE_URL", "DB_URL_ALEMBIC", mode="before")
    @classmethod
    def _normalize_postgres_driver(cls, value):
        if value in (None, ""):
            return value

        db_url = str(value)
        if db_url.startswith("postgresql+psycopg2://"):
            return db_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
        if db_url.startswith("postgresql://"):
            return db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        if db_url.startswith("postgresql+psycopg://"):
            return db_url

        raise ValueError(
            "URL de Postgres invalida: use el driver 'postgresql+psycopg://'."
        )


def _env_name() -> str:
    return os.getenv("ENVIRONMENT", "development")


def _env_file() -> Path:
    return PROJECT_ROOT / f".env.{_env_name()}"


def load_settings() -> Settings:
    env_file = _env_file()
    base_values = dotenv_values(env_file) if env_file.exists() else {}
    merged_values = {**base_values, **os.environ}

    try:
        # Mismo comportamiento local y docker: .env.<ENV> + override por entorno real.
        return Settings(**merged_values)
    except ValidationError as exc:
        lines = [f"Error de configuracion ({env_file.name}):"]
        for err in exc.errors():
            field = ".".join(str(part) for part in err["loc"])
            lines.append(f" - {field}: {err['msg']}")
        raise RuntimeError("\n".join(lines)) from exc


@lru_cache
def get_settings() -> Settings:
    return load_settings()


settings = get_settings()
