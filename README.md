# ContentFactory

**ContentFactory** — веб-приложение для автоматической генерации контента для товаров маркетплейса. Система загружает товары, генерирует текстовые описания, изображения и видео с помощью AI-моделей.

---

## Назначение

Приложение имитирует кабинет продавца маркетплейса и позволяет:

- **Загружать товары** — имитация импорта из маркетплейса (создание 5 товаров с описаниями и изображениями)
- **Генерировать текстовый контент** — посты, видеоописания, CTA для YouTube, ВКонтакте, Rutube
- **Генерировать изображения** — 3 варианта изображений товара в разных сценах (image-to-image)
- **Генерировать видео** — видео 10–20 секунд с человеком, использующим товар (image-to-video)

---

## Стек технологий

| Компонент | Технология |
|-----------|------------|
| Backend | FastAPI, Python 3.12, SQLAlchemy 2.0 (async), Alembic |
| Frontend | React 18, Vite, TypeScript |
| БД | PostgreSQL 16 |
| Контейнеризация | Docker, Docker Compose |

---

## AI-модели

### OpenAI (текст)

| Назначение | Модель | Переменная |
|------------|--------|------------|
| Генерация текстового контента | GPT (gpt-5-mini-2025-08-07) | `OPENAI_MODEL` |
| Промпты для изображений | GPT | — |
| Сценарии для видео | GPT | — |

Используется для: описаний товаров, постов, видеоописаний, CTA, промптов к изображениям и сценариев для видео.

### Replicate (изображения)

| Назначение | Модель | Переменная |
|------------|--------|------------|
| Генерация изображений | stability-ai/stable-diffusion-img2img | `REPLICATE_IMAGE_MODEL` |

Image-to-image: основное фото товара → 3 варианта в разных сценах (студия, кухня и т.п.).

### Replicate (видео)

| Назначение | Модель | Переменная |
|------------|--------|------------|
| Генерация видео (по умолчанию) | kwaivgi/kling-v2.1 | `REPLICATE_VIDEO_MODEL` |
| Альтернатива (короткие видео ~4 сек) | christophy/stable-video-diffusion | `REPLICATE_VIDEO_MODEL` |

**Kling** — 10–20 секунд, реалистичные люди и действия по промпту.  
**Stable Video Diffusion** — ~4 секунды, в основном анимация камеры.

Длительность видео: `REPLICATE_VIDEO_DURATION` (5–20 для Kling).

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

## Миграции базы данных

Миграции выполняются через Alembic. Цепочка: `001` → `002` → `003` → `004` → `005`.

| ID | Название | Описание |
|----|----------|----------|
| 001 | create_products_table | Таблица `products`: id, name, description, category, price, popularity_score, marketplace_url, created_at |
| 002 | add_image_filename | Колонка `image_filename` в products (ссылка на статическое изображение) |
| 003 | create_generated_content | Таблица `generated_content`: id, product_id, content_type (text/image/video), content_text, file_path, status, content_variant, platform, tone, ai_model, created_at |
| 004 | add_content_text_type | Колонка `content_text_type` (short_post, video_description, cta, all) |
| 005 | add_image_data | Колонка `image_data` (BYTEA) для хранения изображений товаров в БД |

### Выполнение миграций

```bash
cd backend
alembic upgrade head
```

Откат последней миграции:

```bash
alembic downgrade -1
```

---

## Структура проекта

```
ContentFactory/
├── backend/                 # FastAPI
│   ├── app/
│   │   ├── core/            # config, database, logging, rate_limit
│   │   ├── models/          # SQLAlchemy модели
│   │   ├── schemas/         # Pydantic схемы
│   │   ├── repositories/    # Доступ к БД
│   │   ├── services/        # Бизнес-логика
│   │   │   ├── ai/          # OpenAI провайдер
│   │   │   ├── image/       # Генерация изображений (Replicate)
│   │   │   ├── video/       # Генерация видео (Replicate)
│   │   │   └── media/       # Хранение медиафайлов
│   │   ├── routers/         # API endpoints
│   │   └── dependencies/
│   ├── migrations/          # Alembic миграции
│   └── Dockerfile
├── frontend/                # React + Vite
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── pages/
│   │   └── services/
│   ├── nginx.conf           # Прокси /api → backend
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## API Endpoints

### Health
- `GET /health` — проверка работы приложения
- `GET /health/db` — проверка подключения к БД

### Products
- `GET /products` — список товаров (фильтры, пагинация)
- `GET /products/{id}` — карточка товара
- `GET /products/{id}/image` — изображение товара
- `PATCH /products/{id}` — обновление товара
- `DELETE /products/{id}` — удаление товара
- `DELETE /products/all` — удаление всех товаров
- `POST /products/import-from-marketplace` — импорт 5 товаров

### Content
- `POST /content/generate/{product_id}` — генерация текстового контента
- `GET /content/product/{product_id}` — список контента по товару
- `GET /content/product/{product_id}/has` — есть ли контент
- `PATCH /content/{id}` — обновление текста (draft)
- `DELETE /content/{id}` — удаление контента
- `POST /content/images/{product_id}` — запуск генерации 3 изображений (async task)
- `POST /content/video/{product_id}` — запуск генерации видео (async task)
- `GET /content/media/{file_path}` — отдача медиафайлов (изображения, видео)

### Tasks
- `GET /tasks/{task_id}` — статус фоновой задачи (pending/running/completed/failed)

---

## Запуск

### Требования

- Docker и Docker Compose
- Файл `.env` (скопировать из `.env.example`)

### Обязательные переменные в .env

```env
POSTGRES_PASSWORD=...          # Пароль PostgreSQL
OPENAI_API_KEY=...             # Ключ OpenAI
REPLICATE_API_TOKEN=...       # Токен Replicate (для изображений и видео)
```

### Запуск через Docker

```bash
cp .env.example .env
# Отредактировать .env, указать ключи

docker compose up -d --build
```

Приложение будет доступно:
- **Frontend:** http://localhost:5173
- **Backend:** http://localhost:8000
- **Swagger:** http://localhost:8000/docs
- **PGAdmin:** http://localhost:5050

### Локальная разработка

**Backend:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
# Настроить DATABASE_URL в .env
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Frontend по умолчанию использует `VITE_API_BASE_URL=/api` — Vite проксирует запросы на backend (см. `vite.config.ts`).

---

## Хранение медиа

- **Изображения товаров:** в БД (`products.image_data`) или статические файлы (`/app/static/images`)
- **Сгенерированные изображения и видео:** в volume `media_data`, путь `/app/media`
  - Изображения: `media/images/{product_id}/{uuid}.png`
  - Видео: `media/videos/{product_id}/{uuid}.mp4`

---

## Rate limiting

Генерация контента ограничена: `CONTENT_GENERATE_RATE_LIMIT` (по умолчанию `10/minute`).

---

## Лицензия

Проект создан в учебных целях.
