# Jaikalki HRMS — Backend (FastAPI)

Backend API for the Jaikalki Technology Pvt Ltd HRMS platform.

## Stack

- FastAPI 0.110, SQLAlchemy 2.0 (async), Pydantic v2
- MySQL 8 (utf8mb4) via aiomysql / pymysql
- Redis 7, Celery
- Alembic migrations
- MinIO (S3-compatible) for files

## Quick start

```bash
# 1. Boot infra (MySQL, Redis, MinIO, phpMyAdmin)
docker-compose up -d mysql redis minio phpmyadmin

# 2. Install Python deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Copy env
cp .env.example .env

# 4. Run migrations (none yet in Phase 0)
alembic upgrade head

# 5. Start the API
uvicorn app.main:app --reload
```

- API:        http://localhost:8000
- Swagger:    http://localhost:8000/docs
- Health:     http://localhost:8000/health
- phpMyAdmin: http://localhost:8080  (root / Love1718)
- MinIO:      http://localhost:9001  (minioadmin / minioadmin)

## Verify DB

```bash
docker exec -it jaikalki_hrms_mysql \
  mysql -u root -pLove1718 db_hrms_jaikalki -e "SHOW DATABASES;"
```

## Tests

```bash
pytest
```

## Project layout

```
app/
  core/         security, permissions, middleware, exceptions
  models/       SQLAlchemy ORM models
  schemas/      Pydantic schemas
  api/v1/       Public/mobile API (versioned)
  api/admin/    Admin-only API
  services/     Business logic (cache, storage, etc.)
  tasks/        Celery tasks
  utils/        Helpers
alembic/        DB migrations
tests/          Pytest suite
static/         Static assets (logos for PDFs etc.)
```
