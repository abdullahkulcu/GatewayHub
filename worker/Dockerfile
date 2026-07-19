# Build context is the repo root (see docker-compose.yml): the worker only
# needs backend/app (poller, db, models, providers) plus its own entrypoint,
# same as `sys.path` wiring in worker/main.py assumes when run locally.
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY worker/ worker/

CMD ["python", "worker/main.py"]
