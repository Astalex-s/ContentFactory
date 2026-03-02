# Деплой с доменом

Локальная разработка — `localhost`. Продакшен — **любой домен** (подтягивается из `.env` на сервере или из GitHub Secrets).

## 1. Откуда берётся домен

| Источник | Когда |
|----------|-------|
| `.env` на сервере | Ручная настройка: `APP_DOMAIN=your-domain.com` или `API_BASE_URL`, `FRONTEND_URL`, `CORS_ORIGINS` |
| GitHub Secret `APP_DOMAIN` | При деплое через Actions — перезаписывает значения в `.env` на сервере |

Если задан `APP_DOMAIN` (в .env или Secret), при деплое автоматически выводятся:
- `API_BASE_URL=https://{домен}/api`
- `FRONTEND_URL=https://{домен}`
- `CORS_ORIGINS=https://{домен}`

## 2. Переменные окружения

**Локально (разработка):**
```bash
cp .env.example .env
# API_BASE_URL, FRONTEND_URL — localhost
```

**На сервере (продакшен):**
```bash
cp .env.production.example .env
# Заполните APP_DOMAIN=your-domain.com (или API_BASE_URL, FRONTEND_URL, CORS_ORIGINS вручную)
# И остальное: POSTGRES_PASSWORD, OAUTH_SECRET_KEY, OPENAI_API_KEY и т.д.
```

**Через GitHub Secrets:**
- Добавьте `APP_DOMAIN` = `your-domain.com` (без https://)
- При каждом деплое эти значения будут записаны в `.env` на сервере

## 3. Nginx

Создайте конфиг для вашего домена (замените `your-domain.com`):

```bash
# Скопируйте nginx-ssl-host.conf.example и замените yourdomain.com на ваш домен
sudo cp nginx-ssl-host.conf.example /etc/nginx/sites-available/contentfactory
# Отредактируйте server_name и пути к сертификатам
sudo ln -s /etc/nginx/sites-available/contentfactory /etc/nginx/sites-enabled/
sudo certbot certonly --nginx -d your-domain.com
sudo nginx -t && sudo systemctl reload nginx
```

Пример: `nginx-ssl-domain.conf.example`.

## 4. OAuth (YouTube, VK)

В настройках OAuth-приложений укажите ваш домен:

| Параметр | Значение |
|----------|----------|
| Authorized JavaScript origins | `https://your-domain.com` |
| Redirect URI (YouTube) | `https://your-domain.com/api/social/callback/youtube` |
| Redirect URI (VK) | `https://your-domain.com/api/social/callback/vk` |

## 5. Сборка и деплой

Frontend: `VITE_API_BASE_URL=/api` — относительный путь, работает с любым доменом.

GitHub Actions:
- **Secret `APP_DOMAIN`** — ваш домен, при деплое подставится в .env
- **Variable `VITE_API_BASE_URL`** = `/api` — для сборки frontend

## 6. Cron: авто-публикация, планирование, статистика

На сервере (тот же хост, что и Docker):

```bash
* * * * * curl -sS -X POST http://127.0.0.1:8000/publish/auto-publish-check
* * * * * curl -sS -X POST http://127.0.0.1:8000/publish/process-pending
*/15 * * * * CONTENTFACTORY_URL=http://127.0.0.1:8000 $DEPLOY_PATH/scripts/refresh_yt_stats.sh
```

- `auto-publish-check` — авто-публикация одобренного контента
- `process-pending` — обработка запланированных публикаций (когда наступило время)
- `refresh_yt_stats` — обновление статистики просмотров из YouTube/VK (каждые 15 мин)

Домен не нужен — backend на localhost.

## 7. Проверка

- Приложение: `https://your-domain.com`
- API docs: `https://your-domain.com/api/docs`
- Health: `curl https://your-domain.com/api/health`
