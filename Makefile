ENV_FILE ?= .env.development

run:
	docker compose --env-file $(ENV_FILE) up --build -d

stop:
	docker compose --env-file $(ENV_FILE) down

lint:
	poetry run ruff check .
	poetry run mypy src

logs:
	docker compose logs -f

build:
	docker compose --env-file $(ENV_FILE) build

shell:
	docker compose --env-file $(ENV_FILE) exec osiris-backend bash

test:
	docker compose --env-file $(ENV_FILE) exec osiris-backend poetry run pytest -v

db-upgrade:
	docker compose --env-file $(ENV_FILE) exec osiris-backend poetry run alembic upgrade head

db-makemigration:
	docker compose --env-file .env.development exec -e ENVIRONMENT=development osiris-backend poetry run alembic revision --autogenerate -m "$(mensaje)"
	docker compose --env-file .env.development exec osiris-backend poetry run alembic upgrade head

db-recreate:
	docker compose --env-file .env.development exec postgres bash -lc '\
	  set -euo pipefail; \
	  if psql -U "$$POSTGRES_USER" -d postgres -h localhost -tAc "SELECT 1 FROM pg_database WHERE datname='\''$$POSTGRES_DB'\''" | grep -q 1; then \
	    psql -U "$$POSTGRES_USER" -d postgres -h localhost -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='\''$$POSTGRES_DB'\''"; \
	    psql -U "$$POSTGRES_USER" -d postgres -h localhost -c "DROP DATABASE \"$$POSTGRES_DB\""; \
	  else \
	    echo \"DB $$POSTGRES_DB no existe, skip DROP\"; \
	  fi'
	docker compose --env-file .env.development exec postgres bash -lc '\
	  set -euo pipefail; \
	  if ! psql -U "$$POSTGRES_USER" -d postgres -h localhost -tAc "SELECT 1 FROM pg_database WHERE datname='\''$$POSTGRES_DB'\''" | grep -q 1; then \
	    psql -U "$$POSTGRES_USER" -d postgres -h localhost -c "CREATE DATABASE \"$$POSTGRES_DB\""; \
	  else \
	    echo \"DB $$POSTGRES_DB ya existe, skip CREATE\"; \
	  fi'
	docker compose --env-file .env.development exec osiris-backend bash -lc 'set -euo pipefail; poetry run alembic upgrade head'
	docker compose --env-file .env.development exec postgres bash -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -h localhost -c "\dt"'
	docker compose --env-file .env.development exec postgres bash -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -h localhost -c "select * from alembic_version;"'

db-reset:
	# DROP condicional (si existe) + matar conexiones abiertas
	docker compose --env-file .env.development exec postgres bash -lc '\
	  set -euo pipefail; \
	  if psql -U "$$POSTGRES_USER" -d postgres -h localhost -tAc "SELECT 1 FROM pg_database WHERE datname='\''$$POSTGRES_DB'\''" | grep -q 1; then \
	    echo ">> Terminating backends for $$POSTGRES_DB"; \
	    psql -U "$$POSTGRES_USER" -d postgres -h localhost -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='\''$$POSTGRES_DB'\''"; \
	    echo ">> Dropping database $$POSTGRES_DB"; \
	    psql -U "$$POSTGRES_USER" -d postgres -h localhost -c "DROP DATABASE \"$$POSTGRES_DB\""; \
	  else \
	    echo ">> DB $$POSTGRES_DB no existe, skip DROP"; \
	  fi'

	# CREATE condicional (solo si no existe)
	docker compose --env-file .env.development exec postgres bash -lc '\
	  set -euo pipefail; \
	  if ! psql -U "$$POSTGRES_USER" -d postgres -h localhost -tAc "SELECT 1 FROM pg_database WHERE datname='\''$$POSTGRES_DB'\''" | grep -q 1; then \
	    echo ">> Creating database $$POSTGRES_DB"; \
	    psql -U "$$POSTGRES_USER" -d postgres -h localhost -c "CREATE DATABASE \"$$POSTGRES_DB\""; \
	  else \
	    echo ">> DB $$POSTGRES_DB ya existe, skip CREATE"; \
	  fi'

	# Verificación: la DB está vacía (sin tablas)
	docker compose --env-file .env.development exec postgres bash -lc '\
	  psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -h localhost -c "\dt" || true'

smoke:
	docker compose --env-file $(ENV_FILE) up -d --build
	poetry run pytest -q tests/smoke
	docker compose --env-file $(ENV_FILE) down

smoke-ci:
	# Levanta la pila (si necesitas que corra en CI; quitar --build si ya está en image cache)
	docker compose --env-file $(ENV_FILE) up -d --build
	# Ejecuta solo las pruebas list-only (seguras para CI)
	poetry run pytest -q tests/smoke/test_list_only.py
	docker compose --env-file $(ENV_FILE) down

seed:
	docker compose --env-file $(ENV_FILE) exec osiris-backend poetry run python scripts/seed_sample_product.py

cleanup-test-data:
	docker compose --env-file $(ENV_FILE) exec osiris-backend poetry run python scripts/cleanup_test_data.py

validate:
	python scripts/validate_setup.py
