FROM node:22-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY app/ ./app/
COPY --from=frontend /build/dist ./static/

ENV APP_DATABASE_URL=postgresql+asyncpg://assistant:assistant@db:5432/assistant

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
