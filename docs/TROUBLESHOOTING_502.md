# Устранение ошибки 502 Bad Gateway и проблем деплоя

## Только postgres остаётся запущенным после деплоя

**Симптом:** После деплоя работают только postgres, backend и frontend не стартуют.

**Причины и решения:**

1. **Миграции упали** — скрипт деплоя выходит на шаге `alembic upgrade head`, до `docker compose up -d` не доходит. Проверьте логи GitHub Actions (шаг "Deploy to server"). На сервере выполните вручную:
   ```bash
   cd $DEPLOY_PATH
   GHCR_OWNER=ваш-username docker compose -f docker-compose.prod.yml --env-file .env run --rm backend alembic stamp head
   GHCR_OWNER=ваш-username docker compose -f docker-compose.prod.yml --env-file .env run --rm backend alembic upgrade head
   GHCR_OWNER=ваш-username docker compose -f docker-compose.prod.yml --env-file .env up -d
   ```

2. **Pull образов с ghcr.io не прошёл (401 Unauthorized)** — для приватного репозитория добавьте в GitHub Secrets секрет `GHCR_TOKEN` (PAT с правом `read:packages`). Deploy автоматически выполнит `docker login ghcr.io` перед pull. Если pull всё равно падает, deploy попытается собрать образы на сервере (fallback).

3. **Образы не собраны** — тег `:latest` пушится только при push в `main`. Убедитесь, что workflow "Build Docker Images" успешно отработал на ветке main. Либо запустите деплой вручную после merge в main.

4. **GHCR_OWNER неверный** — в `.env` на сервере должен быть `GHCR_OWNER=ваш-username` (только lowercase).

---

## Автозапуск контейнеров после перезагрузки сервера

Deploy создаёт systemd-сервис `contentfactory.service` для автозапуска. Если деплой идёт не от root, выполните вручную:

```bash
sudo cp $DEPLOY_PATH/deploy/contentfactory.service /etc/systemd/system/
sudo sed -i "s|__DEPLOY_PATH__|$DEPLOY_PATH|g" /etc/systemd/system/contentfactory.service
sudo systemctl daemon-reload
sudo systemctl enable contentfactory
```

После перезагрузки сервера контейнеры поднимутся автоматически.

---

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

## Postgres: role "root" does not exist

Если в логах postgres видно `FATAL: role "root" does not exist` — кто-то подключается как root (например `pg_isready` без `-U` при deploy). Deploy теперь использует `pg_isready -U $POSTGRES_USER -d $POSTGRES_DB`. При ручной проверке: `docker compose exec postgres pg_isready -U contentfactory -d contentfactory` (подставьте свои значения из .env).

## Ошибка SSH при деплое (kex_exchange_identification: Connection reset by peer)

Если GitHub Actions падает с `kex_exchange_identification: read: Connection reset by peer` или `Connection reset by peer`:

1. **Проверьте ключ в GitHub Secrets** — `SSH_PRIVATE_KEY` должен быть без лишних пробелов/переносов, начинаться с `-----BEGIN` и заканчиваться `-----END OPENSSH PRIVATE KEY-----`.

2. **Сервер: разрешите IP GitHub** — GitHub Actions использует динамические IP. Либо откройте порт 22 для всех (если допустимо), либо добавьте [диапазоны IP GitHub](https://api.github.com/meta) в whitelist.

3. **Сервер: sshd_config** — проверьте `MaxStartups`, `MaxSessions`. Убедитесь, что `AllowUsers`/`AllowGroups` включают пользователя деплоя.

4. **Логи на сервере** — `sudo tail -f /var/log/auth.log` (или `journalctl -u sshd -f`) при запуске деплоя покажет причину сброса.

## Ошибка "Input should be a valid UUID... Field required" при планировании

**Симптом:** При нажатии «Запланировать» или «Опубликовать» возвращается ошибка валидации.

**Какие данные обязательны:**
- **content_id** — UUID видео (выберите видео из списка)
- **account_id** — UUID подключённого аккаунта (YouTube/VK)
- **platform** — youtube или vk
- **scheduled_at** — дата и время (для bulk)

**Проверьте:**
1. Выбрано ли видео в каждой строке (bulk) или в модалке (single)
2. Выбраны ли платформа и аккаунт
3. Указана ли дата/время
4. Подключены ли аккаунты в настройках (Настройки → Социальные сети)
5. Обновите страницу и попробуйте снова

---

## 500 при публикации (Request failed with status code 500)

Если при нажатии «Опубликовать» возвращается 500:

1. **Логи backend** — `docker compose logs --tail=50 backend` покажет traceback (теперь логируется перед возвратом 500).

2. **Частые причины:**
   - Контент или аккаунт не найден (FK) — обновите страницу, переподключите канал.
   - `OAUTH_SECRET_KEY` / `OAUTH_ENCRYPTION_SALT` не заданы или изменены — токены не расшифровываются.
   - Файл видео не найден (local/S3) — проверьте `content.file_path` и доступность медиа.
