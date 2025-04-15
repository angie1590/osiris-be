FROM python:3.10-slim

ENV POETRY_VERSION=2.1.1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y build-essential curl libpq-dev && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
COPY lib ./lib
COPY src ./src
COPY conf ./conf

RUN poetry config virtualenvs.create false && poetry install --no-root

CMD ["poetry", "run", "python", "src/osiris/api/main.py"]
