# Docker — ContentFactory

```bash
cp .env.example .env   # задать OPENAI_API_KEY, REPLICATE_API_TOKEN, пароли
docker compose build
docker compose up -d
```

| Сервис   | Порт | URL                   |
|----------|------|------------------------|
| Frontend | 5173 | http://localhost:5173 |
| Backend  | 8000 | http://localhost:8000 |
| PGAdmin  | 5050 | http://localhost:5050 |

Миграции выполняются при старте backend.
