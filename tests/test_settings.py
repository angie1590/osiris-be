from pathlib import Path

import pytest

from osiris.core import settings as core_settings


def _write_env_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _base_env_lines(environment: str) -> list[str]:
    return [
        f"ENVIRONMENT={environment}",
        "POSTGRES_USER=postgres",
        "POSTGRES_PASSWORD=postgres",
        "POSTGRES_DB=osiris",
        "DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost/osiris",
        "FEEC_AMBIENTE=pruebas",
        "SRI_MODO_EMISION=ELECTRONICO",
        "FEEC_TIPO_EMISION=1",
        "FEEC_REGIMEN=GENERAL",
    ]


def test_load_settings_uses_single_source_and_resolves_relative_cert_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cert_path = tmp_path / "conf" / "firma.p12"
    xsd_path = tmp_path / "conf" / "sri_docs" / "factura_V1_1.xsd"
    cert_path.parent.mkdir(parents=True, exist_ok=True)
    xsd_path.parent.mkdir(parents=True, exist_ok=True)
    cert_path.write_text("dummy", encoding="utf-8")
    xsd_path.write_text("dummy", encoding="utf-8")

    env_file = tmp_path / ".env.e0"
    lines = _base_env_lines("e0") + [
        "FEEC_P12_PATH=conf/firma.p12",
        "FEEC_P12_PASSWORD=clave",
        "FEEC_XSD_PATH=conf/sri_docs/factura_V1_1.xsd",
    ]
    _write_env_file(env_file, "\n".join(lines))

    monkeypatch.setattr(core_settings, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("ENVIRONMENT", "e0")

    loaded = core_settings.load_settings()

    assert loaded.FEEC_P12_PATH == cert_path.resolve()
    assert loaded.FEEC_XSD_PATH == xsd_path.resolve()
    assert loaded.DATABASE_URL.startswith("postgresql+psycopg://")


def test_load_settings_fails_fast_with_clear_message_when_env_var_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cert_path = tmp_path / "conf" / "firma.p12"
    xsd_path = tmp_path / "conf" / "sri_docs" / "factura_V1_1.xsd"
    cert_path.parent.mkdir(parents=True, exist_ok=True)
    xsd_path.parent.mkdir(parents=True, exist_ok=True)
    cert_path.write_text("dummy", encoding="utf-8")
    xsd_path.write_text("dummy", encoding="utf-8")

    env_file = tmp_path / ".env.e0_missing"
    lines = [
        f"ENVIRONMENT=e0_missing",
        "POSTGRES_USER=postgres",
        "POSTGRES_PASSWORD=postgres",
        "POSTGRES_DB=osiris",
        "FEEC_AMBIENTE=pruebas",
        "SRI_MODO_EMISION=ELECTRONICO",
        "FEEC_TIPO_EMISION=1",
        "FEEC_REGIMEN=GENERAL",
        "FEEC_P12_PATH=conf/firma.p12",
        "FEEC_P12_PASSWORD=clave",
        "FEEC_XSD_PATH=conf/sri_docs/factura_V1_1.xsd",
    ]
    _write_env_file(env_file, "\n".join(lines))

    monkeypatch.setattr(core_settings, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("ENVIRONMENT", "e0_missing")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValueError) as exc_info:
        core_settings.load_settings()

    message = str(exc_info.value)
    assert "Error de configuracion (.env.e0_missing):" in message
    assert "DATABASE_URL" in message
    assert "Variable requerida no definida" in message


def test_load_settings_allows_os_environment_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cert_path = tmp_path / "conf" / "firma.p12"
    xsd_path = tmp_path / "conf" / "sri_docs" / "factura_V1_1.xsd"
    cert_path.parent.mkdir(parents=True, exist_ok=True)
    xsd_path.parent.mkdir(parents=True, exist_ok=True)
    cert_path.write_text("dummy", encoding="utf-8")
    xsd_path.write_text("dummy", encoding="utf-8")

    env_file = tmp_path / ".env.e0_override"
    lines = _base_env_lines("e0_override") + [
        "DATABASE_URL=postgresql+psycopg://from_file:pass@localhost/file_db",
        "FEEC_P12_PATH=conf/firma.p12",
        "FEEC_P12_PASSWORD=clave",
        "FEEC_XSD_PATH=conf/sri_docs/factura_V1_1.xsd",
    ]
    _write_env_file(env_file, "\n".join(lines))

    monkeypatch.setattr(core_settings, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("ENVIRONMENT", "e0_override")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://from_env:pass@localhost/env_db",
    )

    loaded = core_settings.load_settings()

    assert loaded.DATABASE_URL == "postgresql+psycopg://from_env:pass@localhost/env_db"


def test_load_settings_normalizes_legacy_postgres_driver_prefixes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cert_path = tmp_path / "conf" / "firma.p12"
    xsd_path = tmp_path / "conf" / "sri_docs" / "factura_V1_1.xsd"
    cert_path.parent.mkdir(parents=True, exist_ok=True)
    xsd_path.parent.mkdir(parents=True, exist_ok=True)
    cert_path.write_text("dummy", encoding="utf-8")
    xsd_path.write_text("dummy", encoding="utf-8")

    env_file = tmp_path / ".env.e0_driver"
    lines = [
        "ENVIRONMENT=e0_driver",
        "POSTGRES_USER=postgres",
        "POSTGRES_PASSWORD=postgres",
        "POSTGRES_DB=osiris",
        "DATABASE_URL=postgresql+psycopg2://from_file:pass@localhost/file_db",
        "DB_URL_ALEMBIC=postgresql://from_file:pass@localhost/alembic_db",
        "FEEC_AMBIENTE=pruebas",
        "SRI_MODO_EMISION=ELECTRONICO",
        "FEEC_TIPO_EMISION=1",
        "FEEC_REGIMEN=GENERAL",
        "FEEC_P12_PATH=conf/firma.p12",
        "FEEC_P12_PASSWORD=clave",
        "FEEC_XSD_PATH=conf/sri_docs/factura_V1_1.xsd",
    ]
    _write_env_file(env_file, "\n".join(lines))

    monkeypatch.setattr(core_settings, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("ENVIRONMENT", "e0_driver")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_URL_ALEMBIC", raising=False)

    loaded = core_settings.load_settings()

    assert loaded.DATABASE_URL == "postgresql+psycopg://from_file:pass@localhost/file_db"
    assert loaded.DB_URL_ALEMBIC == "postgresql+psycopg://from_file:pass@localhost/alembic_db"


def test_load_settings_fails_fast_when_feec_tipo_emision_or_regimen_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cert_path = tmp_path / "conf" / "firma.p12"
    xsd_path = tmp_path / "conf" / "sri_docs" / "factura_V1_1.xsd"
    cert_path.parent.mkdir(parents=True, exist_ok=True)
    xsd_path.parent.mkdir(parents=True, exist_ok=True)
    cert_path.write_text("dummy", encoding="utf-8")
    xsd_path.write_text("dummy", encoding="utf-8")

    env_file = tmp_path / ".env.e0_feec_missing"
    lines = [
        "ENVIRONMENT=e0_feec_missing",
        "POSTGRES_USER=postgres",
        "POSTGRES_PASSWORD=postgres",
        "POSTGRES_DB=osiris",
        "DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost/osiris",
        "FEEC_AMBIENTE=pruebas",
        "SRI_MODO_EMISION=ELECTRONICO",
        "FEEC_P12_PATH=conf/firma.p12",
        "FEEC_P12_PASSWORD=clave",
        "FEEC_XSD_PATH=conf/sri_docs/factura_V1_1.xsd",
    ]
    _write_env_file(env_file, "\n".join(lines))

    monkeypatch.setattr(core_settings, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("ENVIRONMENT", "e0_feec_missing")

    with pytest.raises(ValueError) as exc_info:
        core_settings.load_settings()

    message = str(exc_info.value)
    assert "FEEC_TIPO_EMISION" in message
    assert "FEEC_REGIMEN" in message
    assert "Variable requerida no definida" in message


def test_load_settings_requires_cert_paths_when_sri_modo_emision_is_electronico(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file = tmp_path / ".env.e0_missing_cert_paths"
    lines = [
        "ENVIRONMENT=e0_missing_cert_paths",
        "POSTGRES_USER=postgres",
        "POSTGRES_PASSWORD=postgres",
        "POSTGRES_DB=osiris",
        "DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost/osiris",
        "FEEC_AMBIENTE=pruebas",
        "SRI_MODO_EMISION=ELECTRONICO",
        "FEEC_TIPO_EMISION=1",
        "FEEC_REGIMEN=GENERAL",
    ]
    _write_env_file(env_file, "\n".join(lines))

    monkeypatch.setattr(core_settings, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("ENVIRONMENT", "e0_missing_cert_paths")

    with pytest.raises(ValueError) as exc_info:
        core_settings.load_settings()

    message = str(exc_info.value)
    assert "FEEC_P12_PATH" in message
    assert "FEEC_XSD_PATH" in message


def test_load_settings_allows_non_electronic_mode_without_cert_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file = tmp_path / ".env.e0_non_electronic"
    lines = [
        "ENVIRONMENT=e0_non_electronic",
        "POSTGRES_USER=postgres",
        "POSTGRES_PASSWORD=postgres",
        "POSTGRES_DB=osiris",
        "DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost/osiris",
        "FEEC_AMBIENTE=pruebas",
        "SRI_MODO_EMISION=NO_ELECTRONICO",
        "FEEC_TIPO_EMISION=1",
        "FEEC_REGIMEN=GENERAL",
    ]
    _write_env_file(env_file, "\n".join(lines))

    monkeypatch.setattr(core_settings, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("ENVIRONMENT", "e0_non_electronic")

    loaded = core_settings.load_settings()

    assert loaded.SRI_MODO_EMISION == "NO_ELECTRONICO"
    assert loaded.FEEC_P12_PATH is None
    assert loaded.FEEC_XSD_PATH is None
