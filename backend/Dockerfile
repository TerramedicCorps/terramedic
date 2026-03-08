FROM python:3.14-slim AS builder

RUN pip install --no-cache-dir poetry

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt -o requirements.txt --only main && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.14-slim

# SpatiaLite dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libsqlite3-mod-spatialite \
        gdal-bin \
        libgdal-dev && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SPATIALITE_LIBRARY_PATH=mod_spatialite

# Non-root user
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER app

ENTRYPOINT ["/entrypoint.sh"]
