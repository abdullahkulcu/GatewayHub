# Build context is the repo root (see docker-compose.yml) so this stage can
# also build the frontend static assets that app/main.py serves.
FROM node:22-slim AS frontend-build

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# app/main.py resolves the frontend as ../../frontend/dist relative to this
# file (i.e. a sibling of /app), so it lands here rather than under /app.
COPY --from=frontend-build /frontend/dist /frontend/dist

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
