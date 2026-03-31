FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    NORTHSTAR_DATA_DIR=/data \
    ENABLE_LIVE_CPSC=true \
    ENABLE_LIVE_HEALTH_CANADA=true \
    SESSION_COOKIE_SECURE=true

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY northstar_safety ./northstar_safety
COPY scripts ./scripts
COPY sample-data ./sample-data
COPY run_safety.py ./run_safety.py
COPY run_production.py ./run_production.py
COPY shopify.app.toml.example ./shopify.app.toml.example

RUN mkdir -p /data/uploads /data/backups

VOLUME ["/data"]

EXPOSE 8000

CMD ["python", "run_production.py"]
