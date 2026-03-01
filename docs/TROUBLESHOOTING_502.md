# Устранение ошибки 502 Bad Gateway

## Диагностика

На сервере выполните:

```bash
cd /opt/contentfactory  # или ваш DEPLOY_PATH

# Статус контейнеров
docker compose -f docker-compose.prod.yml ps

# Логи backend (если перезапускается)
docker compose -f docker-compose.prod.yml logs --tail=100 backend

# Логи frontend
docker compose -f docker-compose.prod.yml logs --tail=50 frontend

# Проверка портов
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:5173/
```

## Частые причины

1. **Backend перезапускается** — проверьте логи. Часто: не заданы `OAUTH_SECRET_KEY`, `OAUTH_ENCRYPTION_SALT` или `DATABASE_URL` в `.env`.

2. **Миграции не выполнены** — deploy должен запускать `alembic upgrade head` до старта backend. Если deploy упал на этом шаге, выполните вручную:
   ```bash
   GHCR_OWNER=astalex-s docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
   ```

3. **Nginx не видит upstream** — убедитесь, что в конфиге nginx указаны `127.0.0.1:8000` (backend) и `127.0.0.1:5173` (frontend). Перезагрузите nginx: `sudo nginx -t && sudo systemctl reload nginx`.

4. **Таймаут при старте** — backend может запускаться 30–60 секунд. В nginx добавьте `proxy_connect_timeout 60s; proxy_read_timeout 60s;` (см. nginx-ssl-host.conf.example).
