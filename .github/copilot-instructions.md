# Instrucciones para asistentes de código (Copilot / AGENT)

Resumen rápido
- Proyecto backend en Python 3.10 usando FastAPI + SQLModel/SQLAlchemy.
- Código fuente en `src/osiris`. Punto de entrada: `src/osiris/main.py` (variable `app`).
- Configuración via `pydantic-settings` en `src/osiris/core/settings.py`. Las rutas de archivos (p12, xsd) se resuelven respecto al root del repo.

Qué debe saber un agente para ser útil aquí
- Arquitectura modular: cada dominio está en `src/osiris/modules/common/<nombre>/` y sigue el patrón entity/models/repository/service/router.
- Rutas: los routers se registran en `src/osiris/main.py` y usan el prefijo `/api`.
- CRUD helper: `src/osiris/domain/router.py::register_crud_routes` crea endpoints list/get/create/update/delete esperando que el `service` implemente métodos como `list_paginated`, `get`, `create`, `update`, `delete`.
- DB: `src/osiris/core/db.py` expone `engine` y `get_session()` (dependencia FastAPI). Las sesiones son síncronas y el engine se crea con `postgresql+psycopg`.
- Settings: `load_settings()` busca `.env.<ENVIRONMENT>` (por defecto `development`). Si faltan variables (p.ej. FEEC_P12_PATH) la carga falla con mensaje claro; evita romper ejecuciones cambiando archivos de entorno sin validar.
- Seguridad: hashing de contraseñas en `src/osiris/core/security.py` usa `passlib` bcrypt.
- Facturación electrónica: paquete local `lib/fe_ec-0.1.0-py3-none-any-3.whl` está referenciado en `pyproject.toml` como dependencia `fe-ec`.

Comandos y flujos de desarrollo (comprobados desde README / pyproject)
- Instalar dependencias: `poetry install`.
- Levantar contenedores: `make build` / `make up` (usa el CLI moderno `docker compose` — espacio en lugar de guion).
- Migraciones alembic: crear revisión:
  `PYTHONPATH=src ENVIRONMENT=development poetry run alembic revision --autogenerate -m "mensaje"`
  Aplicar migraciones: `make migrate`.
- Ejecutar pruebas: `make test` (o `poetry run pytest`). `pytest.ini` establece `pythonpath = src`.
- Ejecutar local (desarrollo): con `PYTHONPATH=src` el app es importable como `osiris.main:app`. Ej.:
  `PYTHONPATH=src poetry run uvicorn osiris.main:app --reload --port 8000`

Convenciones y patrones detectables (evitar cambios rupturistas)
- Servicios (`service.py`) reciben siempre una `Session` y devuelven modelos/entidades SQLModel. Mantener esa firma facilita reuso en `register_crud_routes`.
- Evitar importar rutas por path relativo que rompan `PYTHONPATH=src` — el proyecto asume `src` en el path (tests y ejecución usan esto).
- Validaciones de settings lanzan `RuntimeError` con mensajes legibles; si un cambio requiere nuevas variables de entorno, actualiza `.env.development` y documenta en `README.md`.
- No se llaman `SQLModel.metadata.create_all()` automáticamente — la evolución del esquema se hace por Alembic.

Ejemplos concretos en el repo
- CRUD generator: `src/osiris/domain/router.py` (usa `service.list_paginated`, `service.get`, etc.).
- Settings + carga env: `src/osiris/core/settings.py` (importante: rutas relativas → `PROJECT_ROOT`).
- DB session: `src/osiris/core/db.py` (uso de `get_session()` como dependencia FastAPI).
- Punto de entrada: `src/osiris/main.py` (registro de routers y manejo de excepción `NotFoundError`).

Buenas prácticas específicas del proyecto
- Antes de crear migraciones, asegúrate de que `PYTHONPATH=src` y `ENVIRONMENT` estén apuntando al `.env` correcto.
- Para cambios que tocan firma electrónica o rutas a archivos `.p12/.xsd`, valida localmente que `Settings` carga sin errores.
- Mantener compatibilidad con la rueda local `lib/fe_ec-*.whl` o actualizar `pyproject.toml` si la ruta cambia.

Qué pedir a un agente cuando haga cambios
- Ejecutar pruebas unitarias (`make test`) y reportar fallos con stack traces relevantes.
- Verificar que `mypy`/`ruff` no introduzcan errores si se cambia tipado o estilo (`poetry run ruff` / `poetry run mypy`).
- Si modifica `settings` o `db`, incluir pasos de migración en la PR y actualizar `README.md` si hay cambios en los pasos de arranque.

Si algo no es claro o faltan archivos de configuración (p.ej. `.env.development` con claves de prueba), pregunta al mantenedor antes de tocar valores sensibles.

— Fin de instrucción breve —
Por favor revisa si quieres añadir reglas de seguridad específicas (p. ej. políticas de secretos) o ejemplos de PR/branch workflow que deba respetar el agente.
