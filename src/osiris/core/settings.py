from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values
from pydantic import Field, ValidationError, field_validator, model_validator
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
    FEEC_P12_PATH: Path | None = None
    FEEC_P12_PASSWORD: str | None = None
    FEEC_XSD_PATH: Path | None = None
    FEEC_AMBIENTE: str = Field(default="pruebas")  # pruebas | produccion
    SRI_MODO_EMISION: str = Field(default="ELECTRONICO")
    FEEC_TIPO_EMISION: str
    FEEC_REGIMEN: str

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

    @field_validator("SRI_MODO_EMISION")
    @classmethod
    def _check_sri_modo_emision(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in {"ELECTRONICO", "NO_ELECTRONICO"}:
            raise ValueError(
                "SRI_MODO_EMISION debe ser 'ELECTRONICO' o 'NO_ELECTRONICO'"
            )
        return normalized

    @field_validator("FEEC_TIPO_EMISION")
    @classmethod
    def _check_tipo_emision(cls, value: str) -> str:
        if value not in {"1", "2"}:
            raise ValueError("FEEC_TIPO_EMISION debe ser '1' (normal) o '2' (contingencia)")
        return value

    @field_validator("FEEC_REGIMEN")
    @classmethod
    def _check_regimen(cls, value: str) -> str:
        allowed = {
            "GENERAL",
            "CONTRIBUYENTE_ESPECIAL",
            "RIMPE_EMPRENDEDOR",
            "RIMPE_NEGOCIO_POPULAR",
        }
        normalized = value.strip().upper()
        if normalized not in allowed:
            allowed_values = ", ".join(sorted(allowed))
            raise ValueError(f"FEEC_REGIMEN invalido. Valores permitidos: {allowed_values}")
        return normalized

    @model_validator(mode="after")
    def _validate_feec_files(self):
        if self.SRI_MODO_EMISION == "ELECTRONICO":
            missing_fields = []
            if not self.FEEC_P12_PATH:
                missing_fields.append("FEEC_P12_PATH")
            if not self.FEEC_XSD_PATH:
                missing_fields.append("FEEC_XSD_PATH")
            if not self.FEEC_P12_PASSWORD:
                missing_fields.append("FEEC_P12_PASSWORD")

            if missing_fields:
                missing_list = ", ".join(missing_fields)
                raise ValueError(
                    "Variables requeridas cuando SRI_MODO_EMISION=ELECTRONICO: "
                    f"{missing_list}"
                )

        # Si se proveen rutas, validar existencia siempre.
        for field_name in ("FEEC_P12_PATH", "FEEC_XSD_PATH"):
            path_value = getattr(self, field_name)
            if path_value is None:
                continue
            resolved_path = (
                path_value if path_value.is_absolute() else (PROJECT_ROOT / path_value).resolve()
            )
            if not resolved_path.exists():
                raise ValueError(f"Archivo no encontrado en `{field_name}`: {resolved_path}")
            setattr(self, field_name, resolved_path)

        return self

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
            if err.get("type") == "missing":
                lines.append(
                    f" - {field}: Variable requerida no definida en {env_file.name} ni entorno."
                )
            else:
                lines.append(f" - {field}: {err['msg']}")
        raise ValueError("\n".join(lines)) from exc


@lru_cache
def get_settings() -> Settings:
    return load_settings()


settings = get_settings()
