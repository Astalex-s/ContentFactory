# Промпты ContentFactory

Перед выполнением любого промпта:
- Соблюдай PROJECT_RULES.md
- Проверяй актуальность API через MCP context7: resolve-library-id и query-docs
- Используй модели и провайдеры, указанные в промпте

---

## Общие указания

**PROJECT_RULES:** Слои Router → Service → Repository. Бизнес-логика только в Service. Секреты через .env. Изменения БД только через Alembic.

**Context7:** Перед добавлением библиотеки — resolve-library-id, затем query-docs для примеров и параметров. Без проверки библиотека не добавляется.

---

## Этап 1 — Структура и база

### 1.1 Структура проекта

Создай структуру по PROJECT_RULES. Раздели на backend, frontend, database, docs. В backend создай app с папками core, models, schemas, repositories, services, routers, dependencies, interfaces, utils. Добавь migrations и tests. Подключи FastAPI, health endpoint, CORS, базовый logging. Без бизнес-логики и моделей.

### 1.2 PostgreSQL и SQLAlchemy Async

Настрой подключение к PostgreSQL по PROJECT_RULES. Pydantic BaseSettings. DATABASE_URL из .env. Async engine, async_sessionmaker, Base. Dependency get_db.

### 1.3 Модель Product

Создай SQLAlchemy модель Product. Поля: id UUID primary key, name string not null, description text, category string index, price float index, popularity_score float, marketplace_url string, created_at datetime default now. UUID и индексы. Без бизнес-логики.

### 1.4 Alembic

Настрой Alembic для async SQLAlchemy 2.0. Подключи metadata. DATABASE_URL из config. env.py под async. Первая миграция для Product. Проверь создание таблицы.

### 1.5 Pydantic схемы Product

Создай schemas/product. ProductCreate, ProductResponse, ProductFilter. from_attributes=True, price больше нуля, строгая типизация.

### 1.6 Репозиторий Product

Создай ProductRepository. Методы: create, bulk_create, get_all с фильтрацией, check_duplicate. Async, без бизнес-логики. Фильтрация через SQLAlchemy expressions. Пагинация и сортировка.

### 1.7 Сервис импорта CSV

Создай ProductService. Метод import_from_csv. Проверка колонок name, description, category, price, marketplace_url. Валидация, игнорирование дубликатов. popularity_score как 1/price. Сохранение через repository. Возврат отчёта: total_rows, imported, skipped, errors. Без прямого доступа к БД.

### 1.8 Router импорта

Создай router products. POST /products/import. Request и response schema. Dependency injection. Без логики.

### 1.9 Логика популярности

Расширь ProductService. calculate_popularity_score. Приоритет: price меньше 500 — высокий, 500–800 — средний, больше 800 — низкий. Сохранять popularity_score. Без изменения Router.

### 1.10 GET /products с фильтрами

Реализуй GET /products. Фильтры: category, min_price, max_price, sort_by, page, page_size. Пагинация обязательна. Response schema. Без ORM в ответе. Логика в service.

### 1.11 Структура React

Создай frontend на React с Vite. Папки app, pages, components, features, services, hooks, types. Axios с baseURL из .env и interceptors. Без UI логики.

### 1.12 Dashboard

Создай страницу Dashboard. Блок фильтров: category dropdown, min/max price, сортировка, кнопка Применить. Таблица: name, category, price, popularity_score, кнопка Открыть. API только через services.

### 1.13 Карточка товара

Создай страницу ProductDetails. Показать описание, ссылку marketplace, popularity_score. Кнопка «Сгенерировать контент» как заглушка. Без AI логики.

### 1.14 Docker

Настрой Docker и docker-compose. Backend: multi-stage, Python 3.12+, uvicorn, переменные из .env. Frontend: multi-stage, Vite build, nginx или node для статики. Сервисы backend, frontend, postgres, pgadmin. Сеть, volumes, healthchecks. Порты backend 8000, frontend 5173, postgres 5432, pgadmin 5050. Порт 80 не трогать. PGAdmin и PostgreSQL через переменные окружения. Секреты только через .env.

### 1.15 Архитектурная проверка

Проверь проект по PROJECT_RULES. Нет логики в router. Нет доступа к БД вне repository. Секреты через .env. Пагинация обязательна. Нет ORM в ответах. Async корректно. Логирование работает. Нет хардкода. Исправь нарушения.

### 1.16 Интеграционная проверка

Проведи полную проверку этапа 1. Импорт 5 товаров, фильтрация, сортировка, пагинация, логи, миграции, обработка ошибок. Исправь найденные проблемы.

### 1.17 Тесты

Добавь тестирование backend. Настрой pytest. Отдельная test database. Unit tests для ProductService, calculate_popularity_score, import_from_csv. Repository tests. Integration test для POST /products/import и GET /products. Async тесты, не production DB, очистка после выполнения. Сценарии: успешный импорт, дубликаты, неверный CSV, фильтрация, пагинация.

### 1.18 Форма CSV и удаление

На Dashboard: форма загрузки CSV с полем файла, кнопкой Загрузить, отображением результата. Обновление списка после загрузки. Обработка ошибок. Кнопка Удалить в строке с подтверждением. Кнопка Удалить все товары с подтверждением. Backend: DELETE /products/{id}, DELETE /products или /products/all. Методы в repository и service. 404 если товар не найден. По PROJECT_RULES.

---

## Этап 2 — Маркетплейс и карточки

### 2.1 Концепция

Сайт имитирует маркетплейс: загрузка товаров по API, таблица, карточки. Генерация контента — следующий этап.

### 2.2 Кнопка загрузки

Убрать загрузку CSV. Добавить кнопку «Загрузить из маркетплейса». При нажатии POST /products/import-from-marketplace. Показать loading и результат.

### 2.3 Backend импорт

Эндпоинт POST /products/import-from-marketplace. GPT генерирует 5 товаров в JSON. Для каждого GPT формирует промпт для изображения. Replicate генерирует фото. Сохранение в БД: name, description, category, price, popularity_score, marketplace_url, image_data. Описание 2–4 предложения. Поля обязательные. popularity_score по цене. marketplace_url как имитация ссылки. 5 товаров.

### 2.4 Таблица и карточка

В строке: фото, название, категория, цена, популярность. Кнопки Открыть и Удалить. Карточка /products/:id: фото, название, описание, категория, цена, популярность, ссылка. Кнопки Редактировать, Удалить, Создать контент.

### 2.5 Модели

GPT: модель gpt-5-mini-2025-08-07. Генерация товаров и промптов для изображений. Replicate: stability-ai/sdxl. Генерация фото по промпту. Переменные OPENAI_MODEL, REPLICATE_API_TOKEN, IMAGE_PROVIDER.

### 2.6 БД и API

Таблица products: image_data BYTEA nullable. Миграция. API: GET /products, GET /products/{id}, GET /products/{id}/image, POST /products/import-from-marketplace, PATCH /products/{id}, DELETE /products/{id}, DELETE /products/all.

### 2.7 Промпт генерации товаров

Context7: resolve-library-id для openai, query-docs для Chat Completions. GPT через AIProvider. Сервис в marketplace_import. Router только HTTP. Сгенерировать 5 товаров для дома в JSON. Цена 99–1999. Описание 2–4 предложения: материал, преимущества, для кого. Формат: name, description, category, price. Только JSON без markdown.

### 2.8 Промпт для изображения

Context7: query-docs для stability-ai/sdxl. GPT создаёт английский промпт по названию, описанию, категории. Replicate рисует по промпту. Промпт: точный тип товара, визуальные признаки, композиция центр на светлом фоне, стиль product photography. 2–4 предложения. Только текст промпта. Суффикс в коде: professional product photography, white background, studio lighting, 8k, ultra realistic.

---

# ЭТАП 3 — Генерация изображений и видео

## Концепция

Генерация изображений и видео через API (Replicate). GPT — для промптов. Сгенерированный контент на отдельной странице товара. Соблюдать PROJECT_RULES. Использовать context7 для проверки API провайдеров.

---

## 1. Генерация изображений (image-to-image)

### 1.1 Промпты для картинок

- **Модель GPT:** `gpt-5-mini-2025-08-07`
- **Назначение:** формирование детального промпта для Replicate
- **Требования к промпту:**
  - Чёткое описание товара из текущего изображения
  - Товар генерируется **из текущего изображения** — меняется только экспозиция, окружение, фон
  - Внешний вид товара (форма, цвет, текстура) **не меняется**
  - Промпт на английском, 2–4 предложения

### 1.2 Replicate для изображений

- **Провайдер:** Replicate
- **Тип задачи:** image-to-image (изменение окружения/экспозиции при сохранении объекта)
- **Модель:** выбрать через context7 — модель для работы с изображением без изменения внешнего вида объекта (например, смена фона, освещения)
- **Вход:** исходное изображение товара + текстовый промпт от GPT
- **Выход:** PNG, тот же товар в новой сцене

### 1.3 Логика генерации

1. Получить товар (основное изображение из `image_data`)
2. GPT формирует промпт: описание сцены/окружения, без изменения описания самого товара
3. Replicate: image-to-image — передать изображение + промпт
4. Сохранить результат в `generated_content`
5. Генерировать 3 варианта (разные сцены/ракурсы)

---

## 2. Генерация видео

### 2.1 Выбор исходного изображения

- **Функционал:** возможность выбрать, по какой картинке генерировать видео
- **Варианты:** основное фото товара, либо одно из 3 сгенерированных изображений
- **По умолчанию:** если дополнительные изображения не создавались — использовать основное фото из карточки

### 2.2 Replicate для видео

- **Провайдер:** Replicate
- **Тип:** image-to-video
- **Модель:** подобрать через context7 — модель для генерации живого видео, где человек пользуется товаром
- **Длительность:** 15 секунд
- **Требования:** реалистичное видео, без артефактов и галлюцинаций

### 2.3 Сценарий видео (GPT)

- **Модель:** `gpt-5-mini-2025-08-07`
- **Назначение:** сценарий/промпт для видео (человек берёт товар и использует по назначению)
- **Ограничения:** до 120 слов, без выдуманных характеристик

---

## 3. Страница сгенерированного контента

- **Route:** отдельная страница, связанная с товаром (например `/products/:id/content`)
- **Переход:** кнопка «Просмотреть сгенерированный контент» в карточке товара (после генерации)
- **Содержимое:** все сгенерированные изображения и видео для данного товара
- **Действия:** просмотр, удаление по отдельности

---

## 4. Архитектура (без локальных LLM)

### 4.1 Сервисы

- **ImageGenerationService:** получение товара → GPT (промпт) → Replicate (image-to-image) → сохранение
- **VideoGenerationService:** выбор изображения → GPT (сценарий) → Replicate (image-to-video) → сохранение
- **ImagePromptBuilder:** формирование промпта для GPT (описание сцены, не товара)

### 4.2 Очередь задач

- Не выполнять генерацию в router напрямую
- BackgroundTasks или Celery
- Endpoint возвращает `task_id`, статус `pending`
- GET `/tasks/{task_id}` — статусы: pending, running, completed, failed

### 4.3 Router

- POST `/content/images/{product_id}` — генерация 3 изображений
- POST `/content/video/{product_id}` — генерация видео (параметр выбора изображения)
- Только вызов service, rate limit, Pydantic schemas

---

## 5. Хранение медиа

- Структура: `/media/images/{product_id}/`, `/media/videos/{product_id}/`
- Абстракция FileStorageService
- Готовность к замене на S3
- Уникальные имена файлов

---

## 6. Переменные окружения

```
OPENAI_MODEL=gpt-5-mini-2025-08-07
REPLICATE_API_TOKEN=
IMAGE_PROVIDER=replicate
REPLICATE_IMAGE_MODEL=   # image-to-image, выбрать через context7
REPLICATE_VIDEO_MODEL=   # image-to-video, выбрать через context7
REPLICATE_DELAY_SECONDS=15
```

---

## 7. Требования (PROJECT_RULES)

- Слои: Router → Service → Repository
- Бизнес-логика только в Service
- Секреты через .env
- Retry и timeout для API-запросов
- Логирование ошибок
- Context7: перед добавлением моделей Replicate — resolve-library-id, query-docs

---

## 8. Финальный аудит

Проверить: нет логики в router, ключи через .env, retry и timeout, обработка ошибок, SOLID, возможность замены провайдера без изменения сервисов.
Готовность к замене хранилища на S3.

### 3.10 Аудит этапа 3

Проверь после завершения этапа 3:

- Вся бизнес-логика находится только в Service-слое, нет логики в router.
- Все секреты и чувствительные данные (например, ключи API) подгружаются через `.env`, отсутствуют в коде.
- Для всех сторонних API-запросов реализован `timeout` и при необходимости `retry`.
- Ошибки корректно логируются, пользовательские сообщения об ошибках понятны.
- Соблюдены слои: Router → Service → Repository, нет смешения ответственности.
- Все переменные окружения вынесены и используются через настройки.
- Нет хардкода путей, значимые пути и параметры — только через конфигурацию.
- Реализована простая замена любого провайдера (AI, Storage): абстракции для сервисов, поддержка будущей замены S3 для хранения медиа.
- Все эндпоинты валидируют входные данные через Pydantic-схемы.
- Реализованы единый формат ошибок API и удобная обработка на фронте.
- Для генерации изображений и видео корректно реализован rate limit.
- Для генерации медиа: структура файлов /media/images/{product_id}/ и /media/videos/{product_id}/, уникальные имена файлов.
- Задокументированы все переменные окружения (см. выше), они обрабатываются и проверяются на старте приложения.
- Проведен аудит кода на предмет SOLID-принципов и расширяемости.

Итог: после аудита код должен быть готов к масштабированию, легко сопровождаться и изменяться без значительного рефакторинга.

---

## ЭТАП 4 — Интеграция с соцсетями и креаторами

### Концепция

Интеграция YouTube, VK Video и (ограниченно) Rutube через официальные API. OAuth2, публикация видео через backend, очередь публикаций и мониторинг статусов. Backend — FastAPI. Очереди: BackgroundTasks (MVP) с возможностью перехода на Celery. API-провайдеры проверять через context7. Соблюдать PROJECT_RULES. Секреты только через .env.

---

### 4.1 Структура backend

Создай структуру `services/social/`: base_provider.py, youtube_provider.py, vk_provider.py, rutube_provider.py, social_factory.py, oauth_service.py. Принцип: Router → Service → Provider. Provider не знает про HTTP. OAuth в БД, токены шифруются.

### 4.2 Архитектура OAuth

Реализуй OAuth-сервис для подключения соцсетей. Clean Architecture, без логики в router. Токены в БД, шифрование через Fernet (SECRET_KEY из .env). Pydantic Settings. Проверь OAuth YouTube и VK через context7.

Создай: 1) таблицу social_accounts (id, user_id, platform enum, access_token encrypted, refresh_token encrypted, expires_at, created_at); 2) OAuthService: get_auth_url(platform), exchange_code(platform, code), refresh_token(account_id); 3) OAuth 2.0 Authorization Code Flow. Вывести: модель, сервис, миграцию Alembic.

### 4.3 YouTube Provider

Реализуй YouTubeProvider. Проверь через context7: YouTube Data API v3, метод videos.insert, OAuth scope. Используй официальный Google API клиент. Поддержка: title, description, tags, privacyStatus. Обработка квот, retry при 500, таймаут из config. Метод: async upload_video(account_id, file_path, metadata) → {video_id, status, published_at}. Ошибки: логировать отдельно, не возвращать stack trace. Вывести production-ready код provider.

### 4.4 VK Provider

Реализуй VKProvider. Проверь через context7: video.save, upload_url flow. Логика: 1) получить upload_url через video.save; 2) загрузить файл; 3) подтвердить публикацию. Access token через OAuth, проверка прав сообщества, логирование, обработка rate limit. Метод: async upload_video(account_id, file_path, metadata). Вывести код.

### 4.5 Rutube Provider

Реализуй RutubeProvider. Проверь через context7 наличие официального upload API. Если нет — режим read-only: get_channel_videos(), check_video_status(). При невозможности upload — NotImplementedError и комментарий в коде. Вывести код.

### 4.6 Publication Service

Реализуй PublicationService. Логика: пользователь выбирает контент, платформу и дату публикации → добавление в очередь. Таблица publication_queue: id, content_id, platform, account_id, scheduled_at, status (pending, processing, published, failed), error_message, created_at. Методы: schedule_publication(), process_publication(), update_status(). MVP: BackgroundTasks, архитектура с учётом перехода на Celery. Clean Architecture. Вывести код и миграцию.

### 4.7 API Endpoints

Создай endpoints: POST /social/connect/{platform}, GET /social/callback/{platform}, GET /social/accounts, POST /publish/{content_id}, GET /publish/status/{id}. Без бизнес-логики. Pydantic request/response. Проверка авторизации. 404 — аккаунт не найден, 400 — платформа не подключена. Rate limit для публикаций. Вывести router.

### 4.8 Status Sync

Реализуй периодическую проверку статуса публикаций. Проверка статуса видео через API платформ, обновление publication_queue, логирование ошибок. MVP: BackgroundTasks + scheduler. Интерфейс для перехода на Celery. Вывести код.

### 4.9 React UI (social)

Создай feature social/: api.ts, useSocialAccounts.ts, ConnectButton.tsx, PublishModal.tsx, PublicationStatus.tsx. Функционал: подключение аккаунта, просмотр подключённых, выбор платформы, отложенная публикация, статус публикации. Axios instance, baseURL из .env, loading state, error handling, feature-based architecture. Вывести production-ready код.

### 4.10 Переменные окружения (Этап 4)

```
OAUTH_SECRET_KEY=
YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=
VK_CLIENT_ID=
VK_CLIENT_SECRET=
RUTUBE_CLIENT_ID=
RUTUBE_CLIENT_SECRET=
```

### 4.11 Аудит этапа 4

Проверь после завершения этапа 4: вся бизнес-логика в Service, нет логики в router; секреты только через .env; токены шифруются; OAuth flow по документации (context7); очередь публикаций через BackgroundTasks; интерфейс готов к Celery; rate limit для публикаций; ошибки логируются, stack trace не возвращается; 404/400 корректно.

### Итог этапа 4

OAuth подключение, хранение токенов, загрузка видео на YouTube и VK, подготовка к Rutube, очередь публикаций, статусы, возможность масштабирования до Celery, готовность к аналитике (Этап 5).

---

## ЭТАП 5 — Рефакторинг, аудит и документация

### Концепция

Комплексный рефакторинг приложения ContentFactory с фокусом на безопасность, архитектуру и качество кода. Выявление и исправление ошибок и багов. Все изменения — только в соответствии с PROJECT_RULES.md. При добавлении новых библиотек — проверка через MCP context7 (resolve-library-id, query-docs). После выполнения всех действий — полное обновление документации в папке docs/ и README.md. Описания должны быть последовательными и подробными.

---

### 5.1 Рефакторинг приложения

- **Слои:** Router → Service → Repository. Бизнес-логика только в Service. Секреты через .env. Изменения БД только через Alembic.
- **Модульность:** Вынести общее состояние (например, task_store) из роутеров в отдельные сервисы. Убрать циклические зависимости между модулями.
- **Безопасность:** Удалить дефолтные пароли из docker-compose.yml. Секреты (POSTGRES_PASSWORD, PGADMIN_DEFAULT_PASSWORD, OAUTH_SECRET_KEY, OAUTH_ENCRYPTION_SALT) — только через переменные окружения без fallback-значений.
- **Шифрование:** Salt для PBKDF2 — в переменной окружения OAUTH_ENCRYPTION_SALT: str. Обновить все вызовы encrypt_token/decrypt_token.
- **Path traversal:** При отдаче медиафайлов проверять resolved path относительно base path. Использовать Path.resolve(), проверка, что путь внутри MEDIA_BASE_PATH.
- **Типизация:** Полная типизация (Python 3.12+). dict → dict[str, Any], TypedDict. Явные контракты, единый стиль ошибок.

---

### 5.2 Выявление ошибок и неточностей

Провести анализ:

- **Хардкод:** пароли, ключи, токены, DSN в коде, миграциях, сидах, docker-compose.yml.
- **Циклические импорты:** между модулями.
- **Отсутствующая типизация:** в моделях, сервисах, репозиториях.
- **Нарушения модульности:** бизнес-логика в роутерах, SQL в сервисах не через репозиторий, создание зависимостей внутри функции.
- **Проблемы безопасности:** path traversal, отсутствие валидации.
- **Неиспользуемый код:** dead code, неиспользуемые импорты.
- **Отсутствующие валидации:** в Pydantic-схемах (platform enum, scheduled_at, URL, max_length).

---

### 5.3 Исправление ошибок и багов

При выявлении:

- **Исправлять:** все найденные ошибки и баги.
- **Валидация:** Pydantic-схемы: отдельные схемы для Create/Update/Read. Валидация обязательных полей Request на входе.
- **Ошибки:** возвращать в едином формате JSON (code/message/details).
- **Concurrency:** реализация «take in work» должна быть атомарной: один запрос выигрывает, второй получает 409.
- **Сообщения:** 409 — короткое и на русском, без технических деталей (например: «Заявка уже взята в работу»).

---

### 5.4 Соответствие PROJECT_RULES и context7

- **PROJECT_RULES:** Соблюдать все пункты 1–24. Секреты через .env. Изменения БД только через Alembic. Логика только в Service. Слои Router → Service → Repository.
- **Context7:** Перед добавлением библиотеки — resolve-library-id, затем query-docs для примеров и параметров. Без проверки библиотека не добавляется.
- **Code quality:** format (black), lint (ruff), tests (pytest).
- **Git:** main защищён; только merge через PR, обязательный CI green. develop: интеграция. feature/*: работа задач.

---

### 5.5 Обновление документации

После выполнения всех действий по пунктам 5.1–5.4:

- **README.md:** Полное описание функционала приложения, запуск dev/prod, тестовые пользователи, переменные окружения, структура проекта, API endpoints, миграции, безопасность, рекомендации для production.
- **docs/ARCHITECTURE.md:** Архитектура приложения, слои, паттерны (DI, Repository, Service, Factory, Strategy), асинхронность, фоновые задачи, безопасность, БД, масштабирование.
- **docs/SECURITY.md:** Реализованные меры безопасности, рекомендации для production, checklist.
- **docs/DECISIONS.md:** Ключевые архитектурные решения с обоснованием и альтернативами.
- **docs/SOCIAL_PLATFORMS.md:** Обновить при наличии изменений (OAuth, шифрование, переменные окружения).
- **docs/docker.md:** Обновить при наличии изменений в Docker.

---

### 5.6 Формат документации

- **Последовательность:** Описания логически связаны, без противоречий.
- **Подробность:** Каждый раздел содержит достаточную информацию для понимания и воспроизведения.
- **Структура:** Заголовки, списки, таблицы, блоки кода. Единый стиль.
- **Актуальность:** Документация соответствует текущему состоянию кода.

---

### 5.7 Аудит этапа 5

Проверь после завершения этапа 5:

- Вся бизнес-логика находится только в Service-слое, нет логики в router.
- Все секреты и чувствительные данные подгружаются через .env, отсутствуют в коде и docker-compose.
- Нет дефолтных паролей в docker-compose.yml.
- OAUTH_ENCRYPTION_SALT вынесен в переменные окружения.
- Path traversal защита реализована при отдаче медиа.
- Все Pydantic-схемы валидируют входные данные (platform, scheduled_at, URL, max_length).
- Полная типизация в сервисах и репозиториях.
- Общее состояние (task_store) вынесено в отдельный сервис.
- Нет циклических зависимостей между модулями.
- Документация в docs/ и README.md обновлена, последовательна и подробна.
- DECISIONS.md фиксирует ключевые решения и причины (коротко, 5–7 пунктов).

### Итог этапа 5

Рефакторинг завершён, ошибки исправлены, архитектура соответствует PROJECT_RULES, документация обновлена. Приложение готово к дальнейшей разработке и может быть развёрнуто в production после выполнения рекомендаций по безопасности.
