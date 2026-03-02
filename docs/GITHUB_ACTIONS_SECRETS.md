# GitHub Actions — Секреты и переменные

Документ описывает все секреты и переменные, которые необходимо настроить
в GitHub для работы CI/CD пайплайна ContentFactory.

---

## 1. CI (`ci.yml`) — Тесты, линтинг, миграции

CI-пайплайн **не требует настройки секретов**. Все переменные окружения
для тестовой базы данных и плейсхолдеры API-ключей захардкожены прямо
в workflow-файле (используются только для запуска тестов).

| Переменная | Значение в CI | Назначение |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://test_user:test_password@localhost:5432/test_contentfactory` | Тестовая БД (service container) |
| `OPENAI_API_KEY` | `test_key_placeholder` | Плейсхолдер (AI не вызывается в тестах) |
| `REPLICATE_API_TOKEN` | `test_token_placeholder` | Плейсхолдер |
| `OAUTH_SECRET_KEY` | `test_secret_key_for_ci_only` | Тестовый ключ шифрования |
| `OAUTH_ENCRYPTION_SALT` | `test_salt_for_ci_only` | Тестовая соль |
| `STORAGE_BACKEND` | `local` | Локальное хранилище для тестов |
| `MEDIA_BASE_PATH` | `./media` | Относительный путь для тестов |

> Если репозиторий приватный и нужен Codecov, добавьте секрет `CODECOV_TOKEN`
> (получить на [codecov.io](https://codecov.io) после подключения репозитория).

---

## 2. Build (`build.yml`) — Сборка Docker-образов

### Автоматические (не нужно настраивать)

| Секрет | Назначение |
|---|---|
| `GITHUB_TOKEN` | Автоматически предоставляется GitHub Actions. Используется для push образов в ghcr.io |

### Repository Variables (Settings → Variables → Actions)

| Переменная | Обязательная | Значение | Назначение |
|---|---|---|---|
| `VITE_API_BASE_URL` | Нет | `/api` | URL API для frontend (вшивается при сборке). По умолчанию `http://localhost:8000` |

**Где настроить:** GitHub → Settings → Secrets and variables → Actions → Variables tab → New repository variable

---

## 3. Deploy (`deploy.yml`) — Деплой на сервер

### Обязательные секреты (Settings → Secrets → Actions)

| Секрет | Назначение | Где взять |
|---|---|---|
| `SSH_PRIVATE_KEY` | Приватный SSH-ключ для подключения к серверу | `ssh-keygen -t ed25519 -C "deploy"` → содержимое файла `~/.ssh/id_ed25519` (приватный ключ). Публичный ключ добавить в `~/.ssh/authorized_keys` на сервере |
| `SSH_HOST` | IP-адрес или домен сервера | IP вашего VPS/сервера, например `185.123.45.67` |
| `SSH_USER` | Имя пользователя SSH | Пользователь на сервере, например `deploy` или `root` |
| `DEPLOY_PATH` | Абсолютный путь к проекту на сервере | Например `/opt/contentfactory` или `/home/deploy/contentfactory` |

### Опциональные секреты

| Секрет | Назначение | Где взять |
|---|---|---|
| `GHCR_TOKEN` | Токен для pull образов с ghcr.io (приватный репозиторий) | GitHub → Settings → Developer settings → Personal access tokens → создать токен с правом `read:packages`. Без него pull может падать с 401 — тогда deploy соберёт образы на сервере (fallback) |
| `APP_DOMAIN` | Домен приложения (без https://) | При деплое подставит `API_BASE_URL`, `FRONTEND_URL`, `CORS_ORIGINS` в `.env` на сервере. Альтернатива: задать вручную в `.env` на сервере |
| `SSH_PORT` | SSH-порт (по умолчанию `22`) | Если SSH настроен на нестандартном порту |
| `S3_ACCESS_KEY_ID` | Access Key для S3-хранилища | Панель управления облачного провайдера (AWS IAM, DigitalOcean Spaces, MinIO) |
| `S3_SECRET_ACCESS_KEY` | Secret Key для S3-хранилища | Там же |
| `S3_BUCKET` | Имя бакета | Создать в панели управления |
| `S3_REGION` | Регион (по умолчанию `us-east-1`) | Зависит от провайдера |
| `S3_ENDPOINT_URL` | URL эндпоинта (для DigitalOcean Spaces, MinIO) | Например `https://fra1.digitaloceanspaces.com` |
| `S3_PUBLIC_URL` | Публичный URL для доступа к файлам | Например `https://cdn.example.com` или `https://bucket.s3.amazonaws.com` |
| `S3_PRESIGNED_EXPIRE` | Время жизни presigned URL в секундах | По умолчанию `3600` (1 час) |

> При наличии `S3_ACCESS_KEY_ID` и `S3_BUCKET` деплой автоматически переключит
> `STORAGE_BACKEND` на `s3` в `.env` на сервере.

---

## 4. Переменные в `.env` на сервере

Эти переменные должны быть настроены в `.env` файле **на сервере** (в `DEPLOY_PATH`).
Деплой-скрипт **не** управляет ими (кроме S3 и APP_DOMAIN — см. выше).

| Переменная | Обязательная | Пример | Назначение |
|---|---|---|---|
| `POSTGRES_USER` | Да | `contentfactory` | Пользователь PostgreSQL |
| `POSTGRES_PASSWORD` | Да | (сгенерировать) | Пароль PostgreSQL |
| `POSTGRES_DB` | Да | `contentfactory` | Имя базы данных |
| `CORS_ORIGINS` | Да | `https://yourdomain.com` | Разрешённые CORS-домены |
| `OPENAI_API_KEY` | Да | `sk-proj-...` | Ключ OpenAI API → [platform.openai.com](https://platform.openai.com/api-keys) |
| `REPLICATE_API_TOKEN` | Да | `r8_...` | Токен Replicate → [replicate.com/account/api-tokens](https://replicate.com/account/api-tokens) |
| `OAUTH_SECRET_KEY` | Да | (сгенерировать) | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `OAUTH_ENCRYPTION_SALT` | Да | (сгенерировать) | `python -c "import secrets; print(secrets.token_urlsafe(16))"` |
| `GHCR_OWNER` | Да | `astalex-s` | GitHub username (только lowercase — ghcr.io требует) |
| `API_BASE_URL` | Да | `https://yourdomain.com/api` | Базовый URL бэкенда (с `/api` — OAuth callback попадёт в backend) |
| `FRONTEND_URL` | Да | `https://yourdomain.com` | URL фронтенда (редирект после OAuth) |

---

## 5. Как настроить

### Шаг 1: Создать SSH-ключ для деплоя

```bash
ssh-keygen -t ed25519 -C "github-deploy" -f deploy_key
# deploy_key     — приватный ключ (добавить в GitHub Secret SSH_PRIVATE_KEY)
# deploy_key.pub — публичный ключ (добавить на сервер в ~/.ssh/authorized_keys)
```

### Шаг 2: Добавить секреты в GitHub

1. Перейти: **Settings → Secrets and variables → Actions → Secrets tab**
2. Нажать **New repository secret**
3. Добавить каждый секрет из таблиц выше

### Шаг 3: Добавить переменные (Variables)

1. Перейти: **Settings → Secrets and variables → Actions → Variables tab**
2. Нажать **New repository variable**
3. Добавить `VITE_API_BASE_URL` = `/api` (или ваш URL)

### Шаг 4: Подготовить сервер

```bash
# На сервере:
mkdir -p /opt/contentfactory
cd /opt/contentfactory
git clone <your-repo-url> .
cp .env.example .env
# Отредактировать .env — заполнить все обязательные переменные
```

### Шаг 5: Первый деплой

Перейти: **Actions → Deploy to Server → Run workflow → production**

---

## 6. Troubleshooting

**fatal: not a git repository**

Причина: в `DEPLOY_PATH` нет клонированного репозитория.

Решение: на сервере выполнить:
```bash
mkdir -p $DEPLOY_PATH
cd $DEPLOY_PATH
git clone https://github.com/ВАШ-USERNAME/ContentFactory.git .
cp .env.example .env
nano .env   # заполнить POSTGRES_*, GHCR_OWNER и др.
```

---

**PostgreSQL не стартует / dependency failed**

Причина: на сервере нет `.env` или в нём пустые `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`.

Решение: на сервере в `DEPLOY_PATH` выполнить:
```bash
cp .env.example .env
nano .env   # заполнить POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB и остальные обязательные переменные
```

Деплой-скрипт проверяет наличие `.env` и обязательных переменных перед запуском — при ошибке выведет понятное сообщение.

---

**Открывается только страница nginx (Welcome to nginx!)**

Причина: используется nginx на хосте с дефолтным конфигом, а не прокси на frontend/backend.

Решение: настроить host nginx по образцу `nginx-ssl-host.conf.example`:
```bash
# На сервере
sudo cp $DEPLOY_PATH/nginx-ssl-host.conf.example /etc/nginx/sites-available/contentfactory
sudo nano /etc/nginx/sites-available/contentfactory  # заменить yourdomain.com, пути к сертификатам
sudo ln -sf /etc/nginx/sites-available/contentfactory /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Важно: `/api/` → `127.0.0.1:8000`, `/` → `127.0.0.1:5173` (порты Docker). Если открывается дефолтный сайт nginx — отключите его: `sudo rm /etc/nginx/sites-enabled/default`.

---

**invalid reference format: repository name must be lowercase**

Причина: в `.env` указан `GHCR_OWNER` с заглавными буквами (например `Astalex-s`), а ghcr.io требует lowercase.

Решение: в `.env` на сервере указать `GHCR_OWNER=astalex-s` (только строчные). Деплой-скрипт автоматически приводит значение к lowercase, но лучше задать сразу правильно.

---

**OAuth YouTube: пустая страница после авторизации**

Причина: callback попадает на frontend вместо backend (в логах видно `contentfactory-frontend`).

Решение: в `.env` на сервере установить `API_BASE_URL=https://your-domain.com/api` (с `/api`). В Google Cloud Console → Credentials → OAuth client → Authorized redirect URIs добавить `https://your-domain.com/api/social/callback/youtube`. Перезапустить backend: `docker compose --profile ssl up -d`.

---

## 7. Environment-ы (опционально)

Для разделения production/staging можно создать GitHub Environments:

1. **Settings → Environments → New environment**
2. Создать `production` и `staging`
3. Добавить разные значения секретов для каждого environment
4. При ручном деплое выбирать environment в dropdown

Это позволяет иметь разные серверы, базы данных и конфигурации
для production и staging.
