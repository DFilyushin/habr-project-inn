FROM python:3.10-alpine

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN pip install poetry

RUN poetry config installer.max-workers 10 \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY ./src/ /app/