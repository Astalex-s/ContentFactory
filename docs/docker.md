# Docker — ContentFactory

## Быстрый старт (разработка)

```bash
cp .env.example .env   # задать POSTGRES_PASSWORD, OPENAI_API_KEY, REPLICATE_API_TOKEN и др.
docker compose up -d --build
```

Миграции выполняются автоматически при старте backend.

## Сервисы

| Сервис | Порт | URL | Описание |
|--------|------|-----|----------|
| Frontend | 5173 | http://localhost:5173 | React UI |
| Backend | 8000 | http://localhost:8000 | FastAPI API |
| Swagger | 8000 | http://localhost:8000/docs | API документация |
| PostgreSQL | 5432 | localhost:5432 | База данных |
| PGAdmin | 5050 | http://localhost:5050 | Управление БД (профиль dev-tools) |

## Docker Compose файлы

| Файл | Назначение |
|------|------------|
| `docker-compose.yml` | Разработка: postgres + backend + frontend + pgadmin (профиль) |
| `docker-compose.prod.yml` | Production: postgres + backend + frontend (ghcr.io images) |

## Запуск PGAdmin (опционально)

```bash
docker compose --profile dev-tools up -d pgadmin
```

## Production

```bash
docker compose -f docker-compose.prod.yml up -d
```

Подробнее о деплое: [CI_CD.md](CI_CD.md), [GITHUB_ACTIONS_SECRETS.md](GITHUB_ACTIONS_SECRETS.md)
