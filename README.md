# ContentFactory

**ContentFactory** — веб-приложение для автоматической генерации контента для товаров маркетплейса. Система загружает товары, генерирует текстовые описания, изображения и видео с помощью AI-моделей, а также публикует контент в социальные сети (YouTube, VK, TikTok).

---

## Назначение

Приложение имитирует кабинет продавца маркетплейса и позволяет:

- **Загружать товары** — имитация импорта из маркетплейса (создание 5 товаров с описаниями и изображениями через AI)
- **Генерировать текстовый контент** — посты, видеоописания, CTA для YouTube, ВКонтакте, TikTok с учётом тона и платформы
- **Генерировать изображения** — 3 варианта изображений товара в разных сценах (image-to-image через Replicate)
- **Генерировать видео** — видео 5-20 секунд с товаром (image-to-video через Replicate) с автоматическим QR-кодом для ссылки на товар
- **Подключать социальные сети** — OAuth авторизация для YouTube, VK, TikTok с поддержкой нескольких каналов
- **Публиковать контент** — автоматическая загрузка видео в социальные сети с настраиваемыми заголовками и описаниями

---

## Стек технологий

| Компонент | Технология |
|-----------|------------|
| Backend | FastAPI, Python 3.12, SQLAlchemy 2.0 (async), Alembic |
| Frontend | React 18, Vite, TypeScript |
| БД | PostgreSQL 16 |
| Контейнеризация | Docker, Docker Compose |
| Шифрование | Fernet (cryptography) |
| Rate Limiting | SlowAPI |
| Video Processing | FFmpeg, FFprobe |

---

## AI-модели

### OpenAI (текст)

| Назначение | Модель | Переменная |
|------------|--------|------------|
| Генерация текстового контента | GPT (gpt-5-mini-2025-08-07) | `OPENAI_MODEL` |
| Промпты для изображений | GPT | — |
| Сценарии для видео | GPT | — |
| Генерация заголовков видео | GPT | — |

Используется для: описаний товаров, постов, видеоописаний, CTA, промптов к изображениям, сценариев для видео и заголовков.

### Replicate (изображения)

| Назначение | Модель | Переменная |
|------------|--------|------------|
| Генерация изображений | stability-ai/stable-diffusion-img2img | `REPLICATE_IMAGE_MODEL` |

Image-to-image: основное фото товара → 3 варианта в разных сценах (студия, кухня и т.п.).

### Replicate (видео)

| Назначение | Модель | Переменная |
|------------|--------|------------|
| Генерация видео (по умолчанию) | wan-video/wan-2.2-i2v-fast | `REPLICATE_VIDEO_MODEL` |
| Альтернатива (дороже) | google/veo-3.1-fast | `REPLICATE_VIDEO_MODEL` |
| Реалистичные люди | kwaivgi/kling-v2.1 | `REPLICATE_VIDEO_MODEL` |
| Короткие ~4 сек | christophy/stable-video-diffusion | `REPLICATE_VIDEO_MODEL` |

**Wan 2.2 I2V Fast** — дешёвый image-to-video, ~5–7.5 сек, 480p.  
**Veo 3.1 Fast** — 4–8 сек, качественная image-to-video.  
**Kling** — 5–20 сек, реалистичные люди.  
**Stable Video Diffusion** — ~4 сек, анимация камеры.

Длительность: `REPLICATE_VIDEO_DURATION` (Wan: 81-121 frames; Veo: 4|6|8; Kling: 5–20).

---

## Порты

| Сервис | Порт | URL |
|--------|------|-----|
| Frontend | 5173 | http://localhost:5173 |
| Backend API | 8000 | http://localhost:8000 |
| Swagger (API docs) | 8000 | http://localhost:8000/docs |
| PostgreSQL | 5432 | localhost:5432 |
| PGAdmin | 5050 | http://localhost:5050 |

---

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd ContentFactory
```

### 2. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните обязательные переменные:

```bash
cp .env.example .env
```

**Обязательные переменные:**

```env
# База данных
POSTGRES_PASSWORD=your_secure_password

# PGAdmin
PGADMIN_DEFAULT_PASSWORD=your_pgadmin_password

# OpenAI
OPENAI_API_KEY=sk-...

# Replicate
REPLICATE_API_TOKEN=r8_...

# OAuth (для публикации в соцсети)
OAUTH_SECRET_KEY=<base64_fernet_key>
OAUTH_ENCRYPTION_SALT=<random_salt>

# YouTube (опционально)
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...

# VK (опционально)
VK_CLIENT_ID=...
VK_CLIENT_SECRET=...
```

**Генерация ключей шифрования:**

```bash
# OAUTH_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OAUTH_ENCRYPTION_SALT
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

### 3. Запуск через Docker Compose

```bash
docker compose up -d --build
```

Это запустит:
- PostgreSQL (порт 5432)
- Backend (порт 8000)
- Frontend (порт 5173)
- PGAdmin (порт 5050)

### 4. Применение миграций

```bash
docker compose exec backend alembic upgrade head
```

### 5. Открытие приложения

- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- PGAdmin: http://localhost:5050

---

## Миграции базы данных

Миграции выполняются через Alembic. Цепочка: `001` → `002` → `003` → `004` → `005` → `006` → `007` → `008` → `009`.

| ID | Название | Описание |
|----|----------|----------|
| 001 | create_products_table | Таблица `products`: id, name, description, category, price, popularity_score, marketplace_url, created_at |
| 002 | add_image_filename | Колонка `image_filename` в products (ссылка на статическое изображение) |
| 003 | create_generated_content | Таблица `generated_content`: id, product_id, content_type (text/image/video), content_text, file_path, status, content_variant, platform, tone, ai_model, created_at |
| 004 | add_content_text_type | Колонка `content_text_type` (short_post, video_description, cta, all) |
| 005 | add_image_data | Колонка `image_data` (BYTEA) для хранения изображений товаров в БД |
| 006 | create_social_accounts | Таблица `social_accounts` для OAuth-подключённых аккаунтов (YouTube, VK, TikTok) |
| 007 | create_publication_queue | Таблица `publication_queue` для очереди публикаций в соцсети |
| 008 | add_channel_to_social_accounts | Колонки `channel_id` и `channel_title` для поддержки нескольких YouTube каналов |
| 009 | add_title_description_to_publication_queue | Колонки `title` и `description` для метаданных видео |

### Выполнение миграций

```bash
# Применить все миграции
docker compose exec backend alembic upgrade head

# Откатить последнюю миграцию
docker compose exec backend alembic downgrade -1

# Посмотреть текущую версию
docker compose exec backend alembic current

# Посмотреть историю
docker compose exec backend alembic history
```

---

## Структура проекта

```
ContentFactory/
├── backend/                    # FastAPI приложение
│   ├── app/
│   │   ├── core/              # Конфигурация, БД, шифрование, rate limiting
│   │   ├── models/            # SQLAlchemy модели
│   │   ├── schemas/           # Pydantic схемы (DTO)
│   │   ├── repositories/      # Доступ к БД (CRUD)
│   │   ├── services/          # Бизнес-логика
│   │   │   ├── ai/           # AI провайдеры (OpenAI)
│   │   │   ├── image/        # Генерация изображений (Replicate)
│   │   │   ├── video/        # Генерация видео + QR overlay
│   │   │   └── social/       # OAuth и публикация в соцсети
│   │   ├── routers/          # API endpoints
│   │   ├── dependencies.py   # FastAPI dependencies
│   │   └── main.py           # Точка входа
│   ├── migrations/           # Alembic миграции
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # React приложение
│   ├── src/
│   │   ├── features/        # Feature-based структура
│   │   ├── pages/           # Страницы
│   │   └── services/        # API клиенты
│   ├── Dockerfile
│   └── package.json
├── docs/                     # Документация
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## API Endpoints

### Health (`/health`)
- `GET /health` — проверка работы приложения
- `GET /health/db` — проверка подключения к БД

### Products (`/products`)
- `GET /products` — список товаров (фильтры, пагинация)
- `GET /products/{product_id}` — карточка товара
- `GET /products/{product_id}/image` — изображение товара
- `PATCH /products/{product_id}` — обновление товара
- `DELETE /products/{product_id}` — удаление товара
- `DELETE /products/all` — удаление всех товаров
- `POST /products/import-from-marketplace` — импорт 5 товаров (AI)

### Content (`/content`)
- `POST /content/generate/{product_id}` — генерация текста (rate limited: 10/min)
- `POST /content/product/{product_id}/generate-video-title` — генерация заголовка видео
- `GET /content/product/{product_id}` — список контента по товару
- `GET /content/product/{product_id}/has` — проверка наличия контента
- `PATCH /content/{content_id}` — обновление текста (только draft)
- `DELETE /content/{content_id}` — удаление контента
- `POST /content/images/{product_id}` — запуск генерации 3 изображений (async)
- `POST /content/video/{product_id}` — запуск генерации видео (async)
- `GET /content/media/{file_path:path}` — отдача медиафайлов (с поддержкой Range)

### Tasks (`/tasks`)
- `GET /tasks/{task_id}` — статус фоновой задачи

### Social (`/social`)
- `GET /social/connect/{platform}` — URL для OAuth (youtube, vk, tiktok)
- `GET /social/callback/{platform}` — OAuth callback
- `GET /social/accounts` — список подключённых аккаунтов
- `DELETE /social/accounts/{account_id}` — отключение аккаунта

### Publish (`/publish`)
- `GET /publish/` — список публикаций (фильтры: status, platform, пагинация)
- `POST /publish/{content_id}` — запланировать публикацию (rate limited: 5/min)
- `POST /publish/bulk` — массовое планирование публикаций (rate limited: 3/min, max 50)
- `GET /publish/status/{id}` — статус публикации
- `DELETE /publish/{id}` — отменить публикацию (только pending)

Полная документация API: http://localhost:8000/docs

---

## Функционал публикации в соцсети

### Поддерживаемые платформы

- **YouTube** — полная поддержка (OAuth + upload через Data API v3)
- **VK** — полная поддержка (OAuth + upload через video.save API)
- **TikTok** — OAuth реализован, upload недоступен (нет публичного API)

### OAuth Flow

1. Пользователь нажимает "Подключить {platform}" на странице товара
2. Приложение генерирует OAuth URL (`GET /social/connect/{platform}`)
3. Редирект на страницу авторизации платформы
4. После авторизации callback на `GET /social/callback/{platform}`
5. Обмен authorization code на access/refresh tokens
6. Для YouTube: получение channel_id и channel_title
7. Сохранение токенов в БД (зашифровано через Fernet)
8. Редирект на frontend с результатом

### Планирование публикаций

**Страница:** `/publishing` — управление очередью публикаций

**Функционал:**
1. **Выбор контента** — модальное окно с фильтрами (тип, платформа), множественный выбор
2. **Настройка публикаций** — для каждого контента:
   - Платформа (YouTube/VK/TikTok)
   - Аккаунт (из подключённых)
   - Дата и время публикации
   - Заголовок и описание (опционально)
3. **Массовое планирование** — до 50 публикаций за раз через `POST /publish/bulk`
4. **Управление очередью:**
   - Просмотр всех публикаций с фильтрами (статус, платформа)
   - Отмена запланированных публикаций (только pending)
   - Просмотр результатов (ссылки на опубликованные видео)

**Процесс публикации:**
1. Проверка существования файла
2. Обновление токена при необходимости (YouTube токены живут ~1 час)
3. Для длинных видео (≥60 сек): добавление ссылки на товар в описание
4. Для всех видео: QR-код с ссылкой уже в видео (добавлен при генерации)
5. Загрузка через провайдер платформы
6. Обновление статуса в БД

**Статусы публикаций:**
- `pending` — ожидает публикации
- `processing` — в процессе загрузки
- `published` — успешно опубликовано
- `failed` — ошибка при публикации

### Безопасность

- Токены шифруются с помощью Fernet (PBKDF2 + AES)
- Требуются `OAUTH_SECRET_KEY` (Fernet key) и `OAUTH_ENCRYPTION_SALT` (salt для PBKDF2)
- Токены хранятся зашифрованными в БД
- Refresh токены используются для автоматического обновления access токенов
- Проверка владельца аккаунта при отключении

Подробности: `docs/SOCIAL_PLATFORMS.md`

---

## Переменные окружения

### Обязательные

```env
# База данных
POSTGRES_USER=contentfactory
POSTGRES_PASSWORD=          # Обязательно! Не использовать дефолтные значения
POSTGRES_DB=contentfactory

# PGAdmin
PGADMIN_DEFAULT_EMAIL=admin@example.com
PGADMIN_DEFAULT_PASSWORD=   # Обязательно! Не использовать дефолтные значения

# OpenAI
OPENAI_API_KEY=             # Обязательно! API ключ OpenAI
OPENAI_MODEL=gpt-5-mini-2025-08-07

# Replicate
REPLICATE_API_TOKEN=         # Обязательно! API токен Replicate

# OAuth (для публикации в соцсети)
OAUTH_SECRET_KEY=           # Обязательно! Fernet key (base64)
OAUTH_ENCRYPTION_SALT=      # Обязательно! Salt для PBKDF2
```

### Опциональные

```env
# CORS и логирование
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
LOG_LEVEL=INFO
VITE_API_BASE_URL=/api

# AI настройки
AI_TIMEOUT=60
CONTENT_GENERATE_RATE_LIMIT=10/minute

# Replicate настройки
IMAGE_PROVIDER=replicate
REPLICATE_DELAY_SECONDS=15
REPLICATE_IMAGE_MODEL=stability-ai/stable-diffusion-img2img:15a3689ee13b0d2616e98820eca31d4c3abcd36672df6afce5cb6feb1d66087d
REPLICATE_VIDEO_MODEL=wan-video/wan-2.2-i2v-fast
REPLICATE_VIDEO_DURATION=6

# OAuth клиенты (для публикации)
DEFAULT_USER_ID=00000000-0000-0000-0000-000000000001
YOUTUBE_CLIENT_ID=          # Для YouTube
YOUTUBE_CLIENT_SECRET=       # Для YouTube
VK_CLIENT_ID=               # Для VK
VK_CLIENT_SECRET=            # Для VK
TIKTOK_CLIENT_KEY=          # Для TikTok
TIKTOK_CLIENT_SECRET=       # Для TikTok
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
```

---

## CI/CD

ContentFactory использует GitHub Actions для автоматизации непрерывной интеграции и доставки.

### Workflows

- **CI** (`.github/workflows/ci.yml`) — автоматическая проверка кода при каждом push и PR:
  - Backend: lint (ruff), format (black), type check (pyright), tests (pytest)
  - Frontend: lint (eslint), type check (tsc), build
  - Проверка миграций Alembic
- **Build** (`.github/workflows/build.yml`) — сборка и публикация Docker-образов в GitHub Container Registry (ghcr.io)
- **Deploy** (`.github/workflows/deploy.yml`) — автоматический деплой на сервер по SSH после успешной сборки

### Локальные скрипты

- `./scripts/check.sh` — проверка кода перед коммитом (format, lint, tests)
- `./scripts/commit_checked.sh "сообщение"` — проверка и создание коммита в одном шаге

### GitHub Secrets (для деплоя)

Настройте в **Settings → Secrets and variables → Actions**:

| Secret | Назначение |
|--------|------------|
| `SSH_HOST` | Хост сервера (IP или домен) |
| `SSH_USER` | Пользователь для SSH (например `deploy`) |
| `SSH_PRIVATE_KEY` | Приватный SSH-ключ |
| `SSH_PORT` | Порт SSH (по умолчанию 22) |
| `DEPLOY_PATH` | Путь к приложению на сервере (например `/var/www/contentfactory`) |

**Подробная документация:** `docs/CI_CD.md`

---

## Разработка

### Требования

- Docker и Docker Compose
- Python 3.12+ (для локальной разработки)
- Node.js 18+ (для локальной разработки)

### Запуск без Docker (разработка)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Настроить .env
cp .env.example .env

# Запустить PostgreSQL отдельно или через Docker
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
alembic revision -m "description"
# Отредактировать созданный файл в migrations/versions/
alembic upgrade head
```

### Проверка кода перед коммитом

```bash
# Запустить все проверки (format, lint, tests)
./scripts/check.sh

# Проверить и создать коммит в одном шаге
./scripts/commit_checked.sh "добавлена функция импорта товаров"
```

**Важно:** CI не пропустит код с ошибками линтинга или падающими тестами. Используйте локальные скрипты перед push.

---

## Тестирование

### Проверка здоровья приложения

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/db
```

### Импорт тестовых товаров

1. Откройте http://localhost:5173
2. Нажмите "Импортировать товары"
3. Подождите ~30-60 секунд (генерация через AI)

### Генерация контента

1. Выберите товар
2. Нажмите "Генерировать текст" (выберите платформу, тон, тип)
3. Нажмите "Генерировать изображения" (фоновая задача, ~2-3 минуты)
4. Нажмите "Генерировать видео" (фоновая задача, ~5-10 минут)

### Публикация в соцсети

1. Подключите платформу (YouTube, VK или TikTok)
2. Выберите видео
3. Нажмите "Опубликовать"
4. Заполните форму (заголовок, описание)
5. Подтвердите публикацию
6. Проверьте статус публикации

---

## Архитектура

### Backend

- **Clean Architecture**: разделение на models, repositories, services, routers
- **Async/await**: полностью асинхронный код (SQLAlchemy async, httpx)
- **Dependency Injection**: FastAPI dependencies для сервисов
- **Type Safety**: полная типизация (Python 3.12+)
- **Rate Limiting**: защита от перегрузки AI API
- **Background Tasks**: фоновая обработка генерации и публикации

### Frontend

- **Feature-based**: структура по фичам (content, social)
- **TypeScript**: строгая типизация
- **React Hooks**: функциональные компоненты
- **Axios**: HTTP клиент с перехватчиками

### База данных

- **PostgreSQL 16**: основная БД
- **SQLAlchemy 2.0**: ORM с async поддержкой
- **Alembic**: миграции
- **Индексы**: оптимизация запросов (category, price, platform, status)

---

## Безопасность

### Реализованные меры

1. **Секреты в переменных окружения** — нет хардкода паролей, ключей, токенов
2. **Шифрование токенов OAuth** — Fernet (PBKDF2 + AES)
3. **Path traversal защита** — проверка путей при отдаче медиафайлов
4. **Rate limiting** — защита от перегрузки AI API
5. **Валидация входных данных** — Pydantic схемы с ограничениями
6. **CORS** — настраиваемые разрешённые origins
7. **SQL Injection защита** — параметризованные запросы через SQLAlchemy
8. **Проверка владельца** — при отключении аккаунтов

### Требования к production

1. Использовать сильные пароли для `POSTGRES_PASSWORD` и `PGADMIN_DEFAULT_PASSWORD`
2. Сгенерировать уникальные `OAUTH_SECRET_KEY` и `OAUTH_ENCRYPTION_SALT`
3. Настроить HTTPS (nginx + Let's Encrypt)
4. Отключить `DEBUG` режим
5. Использовать Redis для `TaskStatusService` вместо in-memory
6. Настроить Celery для фоновых задач вместо `BackgroundTasks`
7. Настроить мониторинг и логирование (Sentry, ELK)
8. Регулярно обновлять зависимости

---

## Лицензия

MIT

---

## Контакты

Для вопросов и предложений создавайте issue в репозитории.
