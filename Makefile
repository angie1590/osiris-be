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
	docker-compose exec backend bash

test:
	docker-compose exec backend poetry run pytest
