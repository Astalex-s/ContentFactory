# ContentFactory

**ContentFactory** — веб-приложение для автоматической генерации маркетингового контента для товаров маркетплейса. Система загружает товары, генерирует текстовые описания, изображения и видео с помощью AI-моделей, а затем публикует контент в социальные сети (YouTube, VK, TikTok).

---

## Содержание

- [Назначение](#назначение)
- [Стек технологий](#стек-технологий)
- [AI-модели](#ai-модели)
- [Быстрый старт](#быстрый-старт)
- [Порты и сервисы](#порты-и-сервисы)
- [Структура проекта](#структура-проекта)
- [Переменные окружения](#переменные-окружения)
- [Миграции базы данных](#миграции-базы-данных)
- [API Endpoints](#api-endpoints)
- [Функционал](#функционал)
- [Архитектура](#архитектура)
- [Безопасность](#безопасность)
- [Хранение медиа](#хранение-медиа)
- [CI/CD](#cicd)
- [Разработка](#разработка)
- [Тестирование](#тестирование)
- [Документация](#документация)
- [Лицензия](#лицензия)

---

## Назначение

Приложение имитирует кабинет продавца маркетплейса и реализует полный цикл создания и продвижения контента:

1. **Загрузка товаров** — имитация импорта из маркетплейса: AI генерирует 5 товаров с описаниями и изображениями
2. **Генерация текстового контента** — посты, видеоописания, CTA для YouTube, VK, TikTok с учётом тона и платформы
3. **Генерация изображений** — 1 изображение товара в сцене (image-to-image через Replicate)
4. **Генерация видео** — видео 5–20 сек. с товаром (image-to-video через Replicate) с автоматическим QR-кодом со ссылкой на товар
5. **Подключение социальных сетей** — OAuth-авторизация для YouTube, VK, TikTok с поддержкой нескольких каналов/аккаунтов
6. **Публикация контента** — загрузка видео в социальные сети с настраиваемыми заголовками, описаниями и планированием по времени
7. **Аналитика** — сбор метрик (просмотры, клики, CTR), AI-рекомендации по контенту и времени публикаций
8. **Dashboard** — сводная панель с pipeline контента, аналитикой, алертами и AI-рекомендациями

---

## Стек технологий

| Компонент | Технология |
|-----------|------------|
| Backend | FastAPI, Python 3.12, SQLAlchemy 2.0 (async), Alembic |
| Frontend | React 18, Vite, TypeScript |
| БД | PostgreSQL 16 |
| Контейнеризация | Docker, Docker Compose |
| AI (текст) | OpenAI API (gpt-4o-mini) |
| AI (изображения) | Replicate (black-forest-labs/flux-kontext-pro) |
| AI (видео) | Replicate (wan-video/wan-2.2-i2v-fast и др.) |
| Шифрование | Fernet (cryptography, PBKDF2 + AES) |
| Rate Limiting | SlowAPI |
| Video Processing | FFmpeg, FFprobe |
| CI/CD | GitHub Actions |

---

## AI-модели

### OpenAI (текст)

| Назначение | Модель | Переменная |
|------------|--------|------------|
| Генерация текстового контента | gpt-4o-mini | `OPENAI_MODEL` |
| Промпты для изображений | gpt-4o-mini | — |
| Сценарии для видео | gpt-4o-mini | — |
| Генерация заголовков видео | gpt-4o-mini | — |
| AI-рекомендации | gpt-4o-mini | — |

### Replicate (изображения)

| Назначение | Модель | Переменная |
|------------|--------|------------|
| Генерация изображений (img2img) | black-forest-labs/flux-kontext-pro | `REPLICATE_IMAGE_MODEL` |

Основное фото товара → 1 изображение в сцене (студия, кухня и т.п.).

### Replicate (видео)

| Назначение | Модель | Переменная |
|------------|--------|------------|
| Генерация видео (по умолчанию) | wan-video/wan-2.2-i2v-fast | `REPLICATE_VIDEO_MODEL` |
| Альтернатива (качественнее) | google/veo-3.1-fast | `REPLICATE_VIDEO_MODEL` |
| Реалистичные люди | kwaivgi/kling-v2.1 | `REPLICATE_VIDEO_MODEL` |
| Короткие ~4 сек | christophy/stable-video-diffusion | `REPLICATE_VIDEO_MODEL` |

Длительность настраивается через `REPLICATE_VIDEO_DURATION`.

---

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd ContentFactory
```

### 2. Настройка переменных окружения

```bash
cp .env.example .env
```

Откройте `.env` и заполните **обязательные** переменные:

```env
# Пароли (обязательно сгенерировать!)
POSTGRES_PASSWORD=<сильный_пароль>
PGADMIN_DEFAULT_PASSWORD=<пароль_pgadmin>

# AI ключи (обязательно!)
OPENAI_API_KEY=sk-...
REPLICATE_API_TOKEN=r8_...

# OAuth шифрование (обязательно для работы с соцсетями!)
OAUTH_SECRET_KEY=<сгенерировать>
OAUTH_ENCRYPTION_SALT=<сгенерировать>
```

Генерация ключей шифрования:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"   # OAUTH_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(16))"   # OAUTH_ENCRYPTION_SALT
```

### 3. Запуск через Docker Compose

```bash
docker compose up -d --build
```

Это запустит:
- **PostgreSQL** (порт 5432) — база данных
- **Backend** (порт 8000) — FastAPI API
- **Frontend** (порт 5173) — React UI

Миграции БД применяются автоматически при старте backend.

### 4. (Опционально) Запуск PGAdmin

```bash
docker compose --profile dev-tools up -d pgadmin
```

### 5. Открытие приложения

- **Приложение:** http://localhost:5173
- **API документация (Swagger):** http://localhost:8000/docs
- **PGAdmin:** http://localhost:5050 (если запущен)

---

## Порты и сервисы

| Сервис | Порт | URL |
|--------|------|-----|
| Frontend | 5173 | http://localhost:5173 |
| Backend API | 8000 | http://localhost:8000 |
| Swagger (API docs) | 8000 | http://localhost:8000/docs |
| PostgreSQL | 5432 | localhost:5432 |
| PGAdmin (dev) | 5050 | http://localhost:5050 |

---

## Структура проекта

```
ContentFactory/
├── backend/                        # FastAPI приложение
│   ├── app/
│   │   ├── core/                  # Конфигурация, БД, шифрование, rate limiting
│   │   │   ├── config.py          # Pydantic Settings (все переменные)
│   │   │   ├── database.py        # Async engine, session, Base
│   │   │   ├── encryption.py      # Fernet шифрование токенов
│   │   │   ├── logging.py         # Конфигурация логирования
│   │   │   ├── rate_limit.py      # SlowAPI rate limiter
│   │   │   ├── ai_logging.py      # AI-специфичное логирование
│   │   │   └── ai_middleware.py   # Middleware для AI timing
│   │   ├── models/                # SQLAlchemy модели
│   │   ├── schemas/               # Pydantic DTO (Create/Update/Read)
│   │   ├── repositories/          # Доступ к БД (CRUD)
│   │   ├── services/              # Бизнес-логика
│   │   │   ├── ai/               # AI провайдеры (OpenAI, промпты)
│   │   │   ├── image/            # Генерация изображений (Replicate)
│   │   │   ├── video/            # Генерация видео + QR overlay
│   │   │   ├── social/           # OAuth и публикация в соцсети
│   │   │   └── media/            # Хранение файлов (local / S3)
│   │   ├── routers/              # API endpoints
│   │   ├── dependencies/         # FastAPI dependencies (DI)
│   │   ├── interfaces/           # Абстракции (StorageInterface)
│   │   └── main.py               # Точка входа FastAPI
│   ├── migrations/               # Alembic миграции (001–013)
│   ├── tests/                    # pytest тесты
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                      # React приложение
│   ├── src/
│   │   ├── features/             # Feature-based модули
│   │   ├── pages/                # Страницы
│   │   ├── components/           # Общие компоненты
│   │   ├── services/             # API клиенты (Axios)
│   │   ├── hooks/                # Кастомные React хуки
│   │   ├── types/                # TypeScript типы
│   │   └── ui/                   # UI-Kit (theme, layout, components)
│   ├── Dockerfile
│   └── package.json
├── docs/                          # Документация (см. раздел «Документация»)
├── scripts/                       # Скрипты проверки перед коммитом
│   ├── check.sh                  # format + lint + tests
│   └── commit_checked.sh         # check → git commit
├── .github/workflows/             # CI/CD (GitHub Actions)
│   ├── ci.yml                    # Lint, tests, миграции
│   ├── build.yml                 # Сборка Docker-образов → ghcr.io
│   └── deploy.yml                # Деплой на сервер по SSH
├── docker-compose.yml             # Dev-окружение (postgres + backend + frontend)
├── docker-compose.prod.yml        # Production-окружение (ghcr.io images)
├── .env.example                   # Шаблон переменных окружения
└── README.md
```

---

## Переменные окружения

Все переменные описаны в `.env.example`. Ниже — полный список с пояснениями.

**Локальная разработка:** `cp .env.example .env` (localhost).  
**Продакшен с доменом:** `cp .env.production.example .env` — см. [docs/DEPLOYMENT_DOMAIN.md](docs/DEPLOYMENT_DOMAIN.md).

### Обязательные

| Переменная | Описание | Пример |
|------------|----------|--------|
| `POSTGRES_PASSWORD` | Пароль PostgreSQL | (сгенерировать) |
| `OPENAI_API_KEY` | API-ключ OpenAI | `sk-proj-...` |
| `REPLICATE_API_TOKEN` | Токен Replicate | `r8_...` |
| `OAUTH_SECRET_KEY` | Fernet-ключ шифрования OAuth-токенов | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `OAUTH_ENCRYPTION_SALT` | Salt для PBKDF2 | `python -c "import secrets; print(secrets.token_urlsafe(16))"` |

### Опциональные (с дефолтными значениями)

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `POSTGRES_USER` | `contentfactory` | Пользователь PostgreSQL |
| `POSTGRES_DB` | `contentfactory` | Имя базы данных |
| `ENVIRONMENT` | `development` | Окружение (`development` / `production`) |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Разрешённые CORS-домены (через запятую) |
| `LOG_LEVEL` | `INFO` | Уровень логирования |
| `AI_PROVIDER` | `openai` | AI-провайдер для текста |
| `OPENAI_MODEL` | `gpt-4o-mini` | Модель OpenAI |
| `AI_TIMEOUT` | `60` | Таймаут запросов к AI (сек.) |
| `IMAGE_PROVIDER` | `replicate` | Провайдер генерации изображений |
| `REPLICATE_IMAGE_MODEL` | `black-forest-labs/flux-kontext-pro` | Модель image-to-image |
| `REPLICATE_VIDEO_MODEL` | `wan-video/wan-2.2-i2v-fast` | Модель image-to-video |
| `REPLICATE_VIDEO_DURATION` | `6` | Длительность видео |
| `REPLICATE_DELAY_SECONDS` | `15` | Задержка между запросами Replicate |
| `STORAGE_BACKEND` | `local` | Хранение медиа: `local` или `s3` |
| `MEDIA_BASE_PATH` | `/app/media` | Путь к локальному хранилищу медиа |
| `CONTENT_GENERATE_RATE_LIMIT` | `10/minute` | Rate limit генерации контента |
| `DEFAULT_USER_ID` | `00000000-...` | UUID пользователя по умолчанию (MVP) |
| `API_BASE_URL` | `http://localhost:8000` | Базовый URL бэкенда (для OAuth redirect) |
| `FRONTEND_URL` | `http://localhost:5173` | URL фронтенда (редирект после OAuth) |

### S3 (при `STORAGE_BACKEND=s3`)

| Переменная | Описание |
|------------|----------|
| `S3_ACCESS_KEY_ID` | Access Key (AWS IAM, DO Spaces, MinIO) |
| `S3_SECRET_ACCESS_KEY` | Secret Key |
| `S3_BUCKET` | Имя бакета |
| `S3_REGION` | Регион (по умолчанию `us-east-1`) |
| `S3_ENDPOINT_URL` | URL эндпоинта (для MinIO, DO Spaces) |
| `S3_PUBLIC_URL` | Публичный URL для доступа к файлам |
| `S3_PRESIGNED_EXPIRE` | Время жизни presigned URL (сек, по умолчанию 3600) |

### VK (для загрузки видео в сообщество)

| Переменная | Описание |
|------------|----------|
| `VK_SERVICE_KEY` | Сервисный ключ VK |
| `VK_GROUP_ID` | ID сообщества VK |
| `VK_COMMUNITY_TOKEN` | Токен сообщества VK |

> **Важно:** OAuth-приложения (client_id, client_secret для YouTube/VK/TikTok) **не хранятся** в `.env`.
> Они добавляются через UI (Настройки) и хранятся **только в БД** в зашифрованном виде.
> Подробнее: [docs/SOCIAL_PLATFORMS.md](docs/SOCIAL_PLATFORMS.md)

---

## Миграции базы данных

Миграции выполняются автоматически при старте backend. Цепочка: `001` → `002` → ... → `013`.

| ID | Название | Описание |
|----|----------|----------|
| 001 | create_products_table | Таблица `products`: id, name, description, category, price, popularity_score, marketplace_url, created_at |
| 002 | add_image_filename | Колонка `image_filename` в products |
| 003 | create_generated_content | Таблица `generated_content`: content_type, content_text, file_path, status, platform, tone, ai_model |
| 004 | add_content_text_type | Колонка `content_text_type` (short_post, video_description, cta, all) |
| 005 | add_image_data | Колонка `image_data` (BYTEA) для хранения изображений товаров |
| 006 | create_social_accounts | Таблица `social_accounts` для OAuth-подключённых аккаунтов |
| 007 | create_publication_queue | Таблица `publication_queue` для очереди публикаций |
| 008 | add_channel_to_social_accounts | Колонки `channel_id`, `channel_title` (несколько YouTube-каналов) |
| 009 | add_title_description_to_publication_queue | Колонки `title`, `description` для метаданных видео |
| 010 | replace_rutube_with_tiktok | Замена платформы Rutube на TikTok в enum |
| 011 | create_content_metrics | Таблица `content_metrics` для аналитики (views, clicks, CTR) |
| 012 | create_oauth_app_credentials | Таблица `oauth_app_credentials` для хранения OAuth-приложений в БД |
| 013 | add_oauth_app_id_to_social_accounts | FK `oauth_app_credentials_id` в social_accounts |

### Команды

```bash
# Применить все миграции (выполняется автоматически при старте)
docker compose exec backend alembic upgrade head

# Откатить последнюю миграцию
docker compose exec backend alembic downgrade -1

# Посмотреть текущую версию
docker compose exec backend alembic current

# Посмотреть историю
docker compose exec backend alembic history

# Создать новую миграцию
docker compose exec backend alembic revision -m "описание_изменения"
```

---

## API Endpoints

### Health (`/health`)
- `GET /health` — проверка работы приложения
- `GET /health/db` — проверка подключения к БД

### Products (`/products`)
- `GET /products` — список товаров (фильтры: category, min_price, max_price, sort_by; пагинация)
- `GET /products/{product_id}` — карточка товара
- `GET /products/{product_id}/image` — изображение товара
- `PATCH /products/{product_id}` — обновление товара
- `DELETE /products/{product_id}` — удаление товара
- `DELETE /products/all` — удаление всех товаров
- `POST /products/import-from-marketplace` — импорт 5 товаров через AI

### Content (`/content`)
- `POST /content/generate/{product_id}` — генерация текста (rate limited: 10/min)
- `POST /content/product/{product_id}/generate-video-title` — генерация заголовка видео
- `GET /content/product/{product_id}` — список контента по товару
- `GET /content/product/{product_id}/has` — проверка наличия контента
- `PATCH /content/{content_id}` — обновление текста (только draft)
- `DELETE /content/{content_id}` — удаление контента
- `POST /content/images/{product_id}` — генерация 1 изображения (async, BackgroundTasks)
- `POST /content/video/{product_id}` — генерация видео (async, BackgroundTasks)
- `GET /content/media/{file_path:path}` — отдача медиафайлов (Range, path traversal защита)

### Tasks (`/tasks`)
- `GET /tasks/{task_id}` — статус фоновой задачи (pending → running → completed / failed)

### Social (`/social`)
- `GET /social/connect/{platform}` — URL для OAuth (youtube, vk, tiktok)
- `GET /social/callback/{platform}` — OAuth callback
- `GET /social/accounts` — список подключённых аккаунтов
- `DELETE /social/accounts/{account_id}` — отключение аккаунта
- `GET /social/oauth-apps` — список OAuth-приложений
- `POST /social/oauth-apps` — добавление OAuth-приложения
- `PATCH /social/oauth-apps/{id}` — обновление OAuth-приложения
- `DELETE /social/oauth-apps/{id}` — удаление OAuth-приложения

### Publish (`/publish`)
- `GET /publish/` — список публикаций (фильтры: status, platform; пагинация)
- `POST /publish/{content_id}` — запланировать публикацию (rate limited: 5/min)
- `POST /publish/bulk` — массовое планирование (rate limited: 3/min, max 50)
- `POST /publish/auto-publish-check` — проверка авто-публикации (для cron, каждую минуту)
- `POST /publish/process-pending` — обработка запланированных публикаций (для cron, каждую минуту)
- `GET /publish/status/{id}` — статус публикации
- `DELETE /publish/{id}` — отменить публикацию (только pending)

Полная интерактивная документация: http://localhost:8000/docs (локально) или https://{ваш-домен}/api/docs (продакшен)

---

## Функционал

### Импорт товаров

AI (OpenAI) генерирует 5 товаров для дома с описаниями, категориями, ценами и изображениями (Replicate). Товары сохраняются в БД с `popularity_score`, рассчитанным по цене.

### Генерация контента

- **Текст:** посты, видеоописания, CTA — с выбором платформы (YouTube/VK/TikTok) и тона (профессиональный/дружелюбный/продающий)
- **Изображения:** 1 изображение через image-to-image — товар в сцене
- **Видео:** image-to-video с автоматическим QR-кодом со ссылкой на маркетплейс

### Публикация в соцсети

**Поддерживаемые платформы:**
- **YouTube** — полная поддержка (OAuth + загрузка через Data API v3)
- **VK** — полная поддержка (OAuth + загрузка через video.save API)
- **TikTok** — OAuth реализован, загрузка недоступна (ограниченный API)

**Процесс:** выбор контента → выбор платформы и аккаунта → настройка заголовка/описания → планирование по времени → автоматическая публикация.

Подробнее: [docs/PUBLISHING_QUICKSTART.md](docs/PUBLISHING_QUICKSTART.md)

### OAuth-приложения

Учётные данные OAuth-приложений (client_id, client_secret) хранятся **только в БД** в зашифрованном виде. Управление через UI: Настройки → OAuth-приложения.

Подробнее: [docs/SOCIAL_PLATFORMS.md](docs/SOCIAL_PLATFORMS.md)

---

## Архитектура

### Backend (Clean Architecture)

- **Routers** — только HTTP, валидация, вызов Service, без бизнес-логики
- **Services** — вся бизнес-логика, не зависят от FastAPI
- **Repositories** — доступ к БД (CRUD), используют `flush()`, commit — на уровне `get_db`
- **Models** — SQLAlchemy 2.0 async модели
- **Schemas** — Pydantic DTO (Create/Update/Read)
- **Dependencies** — FastAPI Depends() для DI

### Паттерны

- **Dependency Injection** — все зависимости через FastAPI Depends()
- **Repository Pattern** — изоляция БД от бизнес-логики
- **Factory Pattern** — выбор провайдеров (AI, Social) через конфигурацию
- **Strategy Pattern** — абстракции для AI, Storage, Social провайдеров
- **Service Layer** — бизнес-логика в отдельных сервисах

### Frontend (Feature-based)

- **Feature-based** структура по функциональным модулям
- **TypeScript** — строгая типизация
- **Axios** — HTTP-клиент с перехватчиками
- **React Hooks** — переиспользуемая логика

### Async

Весь backend полностью асинхронный: FastAPI, SQLAlchemy async, httpx, asyncio.

Подробнее: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Безопасность

### Реализованные меры

1. **Секреты в переменных окружения** — нет хардкода паролей, ключей, токенов
2. **Шифрование OAuth-токенов** — Fernet (PBKDF2 + AES) перед сохранением в БД
3. **Path traversal защита** — проверка путей при отдаче медиафайлов
4. **Rate limiting** — SlowAPI для защиты AI API от перегрузки
5. **Валидация входных данных** — Pydantic-схемы с ограничениями (max_length, enum, regex)
6. **CORS** — настраиваемые разрешённые origins через `CORS_ORIGINS`
7. **SQL Injection защита** — параметризованные запросы через SQLAlchemy ORM
8. **Проверка владельца ресурса** — при отключении аккаунтов (user_id)
9. **asyncio.Lock** — thread-safe in-memory хранилище статусов задач

### Рекомендации для production

1. HTTPS через nginx + Let's Encrypt
2. Сильные уникальные пароли для всех сервисов
3. `ENVIRONMENT=production`, `DEBUG=False`
4. Redis для `TaskStatusService` вместо in-memory
5. Celery для фоновых задач вместо BackgroundTasks
6. Мониторинг (Sentry, Prometheus, ELK)
7. Регулярное обновление зависимостей

Подробнее: [docs/SECURITY.md](docs/SECURITY.md)

---

## Хранение медиа

| Режим | Переменная | Назначение |
|-------|------------|------------|
| `local` | `STORAGE_BACKEND=local` | Локальная FS (разработка) |
| `s3` | `STORAGE_BACKEND=s3` | S3-совместимое хранилище (production) |

Переключение через `STORAGE_BACKEND`. Сервисы не зависят от конкретного бэкенда — используется `StorageInterface`.

Поддерживаемые S3 сервисы: AWS S3, MinIO, DigitalOcean Spaces, Yandex Object Storage.

Подробнее: [docs/STORAGE.md](docs/STORAGE.md)

---

## CI/CD

ContentFactory использует **GitHub Actions** для автоматизации:

| Workflow | Файл | Назначение |
|----------|------|------------|
| CI | `.github/workflows/ci.yml` | Lint (black, ruff), type check (pyright), tests (pytest), frontend lint + build, проверка миграций |
| Build | `.github/workflows/build.yml` | Сборка Docker-образов → GitHub Container Registry (ghcr.io) |
| Deploy | `.github/workflows/deploy.yml` | Деплой на сервер по SSH после успешной сборки |

**Принципы:**
- Деплой только при зелёном CI (все тесты прошли)
- Все секреты только через GitHub Secrets
- CI не деплоит при падающих тестах

**Деплой с доменом:** [docs/DEPLOYMENT_DOMAIN.md](docs/DEPLOYMENT_DOMAIN.md) — домен из `.env` (APP_DOMAIN) или GitHub Secret `APP_DOMAIN`, nginx, OAuth, cron.

### GitHub Secrets для деплоя

| Secret | Назначение |
|--------|------------|
| `SSH_HOST` | Хост сервера (IP или домен) |
| `SSH_USER` | Пользователь для SSH |
| `SSH_PRIVATE_KEY` | Приватный SSH-ключ |
| `DEPLOY_PATH` | Путь к приложению на сервере |

Подробный список всех секретов и переменных: [docs/GITHUB_ACTIONS_SECRETS.md](docs/GITHUB_ACTIONS_SECRETS.md)

Полная документация CI/CD: [docs/CI_CD.md](docs/CI_CD.md)

### Локальные скрипты проверки

```bash
# Проверить код перед коммитом (format, lint, tests)
./scripts/check.sh

# Проверить и создать коммит в одном шаге
./scripts/commit_checked.sh "описание изменений"

# Установить pre-push hook (проверки перед каждым git push)
./scripts/install-hooks.sh
```

---

## Разработка

### Требования

- **Docker** и **Docker Compose** (для запуска через контейнеры)
- **Python 3.12+** (для локальной разработки backend)
- **Node.js 18+** (для локальной разработки frontend)

### Запуск через Docker (рекомендуется)

```bash
cp .env.example .env
# Заполнить .env (POSTGRES_PASSWORD, OPENAI_API_KEY, REPLICATE_API_TOKEN и др.)
docker compose up -d --build
```

### Запуск без Docker

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Запустить PostgreSQL отдельно (Docker или локально)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:16

# Применить миграции
alembic upgrade head

# Запустить сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Создание новой миграции

```bash
cd backend
alembic revision -m "описание_изменения"
# Отредактировать файл в migrations/versions/
alembic upgrade head
```

### Production

Для production используйте `docker-compose.prod.yml`:

```bash
docker compose -f docker-compose.prod.yml up -d
```

Подробнее о Docker-окружении: [docs/docker.md](docs/docker.md)

---

## Тестирование

### Проверка здоровья

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/db
```

### Импорт тестовых товаров

1. Откройте http://localhost:5173
2. Нажмите «Импортировать товары»
3. Подождите ~30–60 секунд (AI генерирует 5 товаров с изображениями)

### Генерация контента

1. Выберите товар из списка
2. **Текст:** нажмите «Генерировать текст» (выберите платформу, тон, тип)
3. **Изображения:** нажмите «Генерировать изображения» (фоновая задача, ~2–3 мин.)
4. **Видео:** нажмите «Генерировать видео» (фоновая задача, ~5–10 мин.)

### Публикация в соцсети

1. Добавьте OAuth-приложение в Настройках (client_id, client_secret)
2. Подключите аккаунт на странице Creators
3. Выберите видео на странице Publishing
4. Настройте заголовок, описание, время
5. Нажмите «Запланировать»

---

## Документация

Вся документация проекта расположена в папке `docs/`:

| Документ | Описание |
|----------|----------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Архитектура приложения: слои, паттерны, асинхронность, БД, масштабирование |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Ключевые архитектурные решения с обоснованием и альтернативами |
| [docs/SECURITY.md](docs/SECURITY.md) | Реализованные меры безопасности и рекомендации для production |
| [docs/SOCIAL_PLATFORMS.md](docs/SOCIAL_PLATFORMS.md) | Настройка OAuth для YouTube, VK, TikTok (пошаговая инструкция) |
| [docs/STORAGE.md](docs/STORAGE.md) | Хранение медиафайлов: local vs S3, настройка, миграция |
| [docs/CI_CD.md](docs/CI_CD.md) | CI/CD через GitHub Actions: workflows, секреты, настройка сервера |
| [docs/GITHUB_ACTIONS_SECRETS.md](docs/GITHUB_ACTIONS_SECRETS.md) | Полный список секретов и переменных для GitHub Actions |
| [docs/PUBLISHING_QUICKSTART.md](docs/PUBLISHING_QUICKSTART.md) | Быстрый старт: планирование и управление публикациями |
| [docs/PUBLISHING_QUEUE.md](docs/PUBLISHING_QUEUE.md) | Техническая документация очереди публикаций (API, логика, статусы) |
| [docs/CONTENT_SELECTOR_FEATURES.md](docs/CONTENT_SELECTOR_FEATURES.md) | ContentSelector — модальное окно выбора контента для публикации |
| [docs/CHANGELOG_PUBLISHING.md](docs/CHANGELOG_PUBLISHING.md) | Changelog системы планирования публикаций |
| [docs/docker.md](docs/docker.md) | Docker: быстрый старт и порты |

---

## Лицензия

MIT

---

## Контакты

Для вопросов и предложений создавайте issue в репозитории.
