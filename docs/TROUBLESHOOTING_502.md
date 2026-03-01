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

2. **Миграции не выполнены или "Can't locate revision"** — если БД содержит ревизию, которой нет в коде (например 016 после отката), выполните:
   ```bash
   cd /opt/contentfactory
   GHCR_OWNER=astalex-s docker compose -f docker-compose.prod.yml --env-file .env run --rm backend alembic stamp head
   GHCR_OWNER=astalex-s docker compose -f docker-compose.prod.yml --env-file .env run --rm backend alembic upgrade head
   GHCR_OWNER=astalex-s docker compose -f docker-compose.prod.yml --env-file .env up -d
   ```

3. **Nginx не видит upstream** — убедитесь, что в конфиге nginx указаны `127.0.0.1:8000` (backend) и `127.0.0.1:5173` (frontend). Перезагрузите nginx: `sudo nginx -t && sudo systemctl reload nginx`.

4. **Таймаут при старте** — backend может запускаться 30–60 секунд. В nginx добавьте `proxy_connect_timeout 60s; proxy_read_timeout 60s;` (см. nginx-ssl-host.conf.example).

## Ошибка SSH при деплое (kex_exchange_identification: Connection reset by peer)

Если GitHub Actions падает с `kex_exchange_identification: read: Connection reset by peer` или `Connection reset by peer`:

1. **Проверьте ключ в GitHub Secrets** — `SSH_PRIVATE_KEY` должен быть без лишних пробелов/переносов, начинаться с `-----BEGIN` и заканчиваться `-----END OPENSSH PRIVATE KEY-----`.

2. **Сервер: разрешите IP GitHub** — GitHub Actions использует динамические IP. Либо откройте порт 22 для всех (если допустимо), либо добавьте [диапазоны IP GitHub](https://api.github.com/meta) в whitelist.

3. **Сервер: sshd_config** — проверьте `MaxStartups`, `MaxSessions`. Убедитесь, что `AllowUsers`/`AllowGroups` включают пользователя деплоя.

4. **Логи на сервере** — `sudo tail -f /var/log/auth.log` (или `journalctl -u sshd -f`) при запуске деплоя покажет причину сброса.
