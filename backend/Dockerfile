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

WORKDIR /app

RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-interaction

COPY . .

EXPOSE 8000

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
