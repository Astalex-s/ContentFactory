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
