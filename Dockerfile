FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.1.1 \
    PYTHONPATH=/app \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --no-root

COPY src/ ./src/
COPY manage.py ./
COPY scripts/ ./scripts/

RUN chmod +x scripts/*.sh

EXPOSE 8000

ENTRYPOINT ["./scripts/entrypoint.sh"]

CMD ["gunicorn", "src.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
