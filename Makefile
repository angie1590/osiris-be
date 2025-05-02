ENV_FILE ?= .env.development

run:
	docker-compose --env-file $(ENV_FILE) up --build

stop:
	docker-compose down

logs:
	docker-compose logs -f

build:
	docker-compose --env-file $(ENV_FILE) build

shell:
	docker-compose --env-file $(ENV_FILE) exec osiris-backend bash

test:
	poetry run pytest

db-upgrade:
	docker-compose --env-file $(ENV_FILE) exec osiris-backend poetry run alembic upgrade head

db-makemigration:
	docker-compose --env-file .env.development exec osiris-backend bash -c "PYTHONPATH=src ENVIRONMENT=development poetry run alembic revision --autogenerate -m '$(mensaje)'"

