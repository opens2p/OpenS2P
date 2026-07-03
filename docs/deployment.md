# Deployment

## Local Development

Requirements

- Python 3.12+
- Docker
- Docker Compose
- MariaDB

## Start

```
docker compose up
```

## Backend

```
uvicorn app.main:app --reload
```

## Database Migration

```
alembic upgrade head
```

## Production

Recommended

- Ubuntu Linux
- Docker
- Nginx
- HTTPS
- Daily backups
