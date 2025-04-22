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
	docker-compose --env-file $(ENV_FILE) exec osiris-backend poetry run pytest

migrate:
	docker-compose --env-file $(ENV_FILE) exec osiris-backend poetry run alembic upgrade head
