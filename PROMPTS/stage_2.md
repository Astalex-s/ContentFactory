# ЭТАП 2 — Загрузка товаров с маркетплейса и карточки товаров

## Концепция

Сайт имитирует работу с маркетплейсом: загрузка товаров по API из кабинета продавца, отображение в таблице, карточки товаров с действиями. Генерация контента — следующий этап.

---

## 1. Загрузка товаров с маркетплейса

### 1.1 Кнопка на фронтенде

- **Убрать**: загрузку CSV-файла
- **Добавить**: кнопку «Загрузить из маркетплейса» (имитация API кабинета продавца)
- При нажатии вызывается `POST /products/import-from-marketplace`
- Показывать loading и результат (успех/ошибки)

### 1.2 Backend: импорт с маркетплейса

**Эндпоинт:** `POST /products/import-from-marketplace`

**Логика:**
1. GPT (модель `gpt-5-mini-2025-08-07`) генерирует 5 товаров в JSON
2. Для каждого товара GPT формирует промпт для генерации изображения
3. Replicate (модель `stability-ai/sdxl`) генерирует фото товара
4. Товар сохраняется в БД: name, description, category, price, popularity_score, marketplace_url, **image_data** (бинарные данные изображения)

**Требования к описанию товара:**
- Подробное, но не слишком длинное
- Не одним предложением — 2–4 предложения
- Название, цена, категория, популярность — обязательные поля

**Поля товара:**
- `name` — название
- `description` — описание (2–4 предложения)
- `category` — категория
- `price` — цена
- `popularity_score` — расчёт по цене (price < 500 → 1.0, 500–800 → 0.5, >800 → 0.2)
- `marketplace_url` — имитация ссылки (например `https://marketplace.example/product/{id}`)
- `image_data` — бинарные данные PNG, связаны с товаром

**Количество:** 5 товаров

---

## 2. Таблица товаров (Dashboard)

- В каждой строке: фото, название, категория, цена, популярность
- **Кнопка «Открыть»** — переход на карточку товара `/products/{id}`
- **Кнопка «Удалить»** — удаление товара с подтверждением

---

## 3. Карточка товара (отдельная страница)

**Route:** `/products/:id`

**Содержимое:**
- Фото товара (из `image_data` или endpoint `GET /products/{id}/image`)
- Название, описание, категория, цена, популярность
- Ссылка на маркетплейс
- **Кнопки:**
  - Редактировать
  - Удалить
  - Создать контент (переход на следующий этап — генерация контента)

---

## 4. Модели и провайдеры

### 4.1 GPT

- **Модель:** `gpt-5-mini-2025-08-07`
- **Использование:** генерация товаров, промпты для изображений
- **Переменная:** `OPENAI_MODEL=gpt-5-mini-2025-08-07`

### 4.2 Replicate (изображения)

- **Модель:** `stability-ai/sdxl` (экономичная, хорошее качество для товаров)
- **Использование:** генерация фото товаров по текстовому промпту
- **Переменные:** `REPLICATE_API_TOKEN`, `IMAGE_PROVIDER=replicate`

---

## 5. Структура БД

**Таблица products:**
- `id`, `name`, `description`, `category`, `price`, `popularity_score`, `marketplace_url`, `created_at`
- `image_data` — `BYTEA` (LargeBinary), nullable, изображение в бинарном виде

**Миграция:** добавить колонку `image_data` (если её нет)

---

## 6. API

| Метод | Путь | Описание |
|-------|------|----------|
| GET | /products | Список товаров (фильтры, пагинация) |
| GET | /products/{id} | Карточка товара (без image_data в JSON) |
| GET | /products/{id}/image | Изображение товара (Content-Type: image/png) |
| POST | /products/import-from-marketplace | Импорт 5 товаров (GPT + Replicate) |
| PATCH | /products/{id} | Редактирование товара |
| DELETE | /products/{id} | Удаление товара |
| DELETE | /products/all | Удаление всех товаров |

---

## 7. Переменные окружения (.env)

```
# OpenAI (GPT для товаров и промптов изображений)
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5-mini-2025-08-07
AI_TIMEOUT=60

# Replicate (генерация изображений товаров)
REPLICATE_API_TOKEN=
IMAGE_PROVIDER=replicate
```

---

## 8. Тестирование

- Все тесты выполняются через Docker
- Локальное тестирование (pytest вне Docker, скрипты) — удалить

---

## 9. Файлы для создания/изменения

**Backend:**
- `app/models/product.py` — добавить `image_data`
- `app/repositories/product.py` — поддержка image_data
- `app/services/marketplace_import.py` — сервис импорта (GPT + Replicate)
- `app/services/image/replicate_provider.py` — провайдер Replicate
- `app/routers/products.py` — endpoints import-from-marketplace, image, patch
- `app/core/config.py` — OPENAI_MODEL, REPLICATE_API_TOKEN
- Миграция Alembic — колонка image_data

**Frontend:**
- `DashboardPage.tsx` — кнопка «Загрузить из маркетплейса», убрать CSV
- `ProductDetailsPage.tsx` — карточка с кнопками Редактировать, Удалить, Создать контент
- `products.ts` — `importFromMarketplace()`, `updateProduct()`
- Отображение фото из `/products/{id}/image`

---

## 10. Промпты для GPT

### Генерация товаров

```
Сгенерируй ровно 5 товаров для дома в формате JSON-массива.

Товары ТОЛЬКО для дома и быта: полезные, часто покупаемые, практичные.
Цена: от 99 до 1999 рублей.

Описание: 2–4 предложения. Подробно, но не одним предложением. Включи:
- Материал и качество
- Преимущества и применение
- Для кого подойдёт

Формат каждого элемента:
{
  "name": "Название",
  "description": "Описание 2–4 предложения.",
  "category": "Категория",
  "price": число от 99 до 1999
}

Верни ТОЛЬКО валидный JSON-массив, без markdown.
```

### Промпт для изображения (английский, для Replicate SDXL)

```
For product: {name}. {description}
Generate: Hyperrealistic product photography. 
Ultra realistic, photorealistic, professional e-commerce. 
White or light neutral background, natural soft lighting. 
Single product centered, sharp focus, 8k, detailed texture.
```
