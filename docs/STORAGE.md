# Хранение медиафайлов

Документация по хранению сгенерированных изображений и видео (Этап 10).

---

## Обзор

ContentFactory поддерживает два бэкенда хранения медиа:

| Бэкенд | Назначение | Переменная |
|--------|------------|------------|
| `local` | Разработка, тесты | `STORAGE_BACKEND=local` |
| `s3` | Production | `STORAGE_BACKEND=s3` |

Переключение осуществляется через переменную окружения `STORAGE_BACKEND`. Сервисы и роутеры не зависят от конкретного бэкенда — используется единый интерфейс `StorageInterface`.

---

## Архитектура

### Интерфейс StorageInterface

Все операции с медиа выполняются через абстракцию:

- `upload(key, data, content_type)` — загрузка, возвращает ключ
- `download(key)` — скачивание по ключу
- `get_url(key)` — URL для доступа (публичный или presigned)
- `delete(key)` — удаление
- `exists(key)` — проверка существования

### Структура ключей в хранилище

```
images/{product_id}/{uuid}.png   — сгенерированные изображения
videos/{product_id}/{uuid}.mp4   — сгенерированные видео
```

Ключ сохраняется в БД (`generated_content.file_path`) и используется для доступа к файлу.

---

## Локальное хранилище (local)

### Настройка

```env
STORAGE_BACKEND=local
MEDIA_BASE_PATH=./media
```

Файлы сохраняются в директорию `MEDIA_BASE_PATH`. При отдаче используется `FileResponse` с поддержкой Range (для видео).

### Безопасность

Реализована защита от path traversal: разрешены только пути внутри `MEDIA_BASE_PATH`. Проверка выполняется через `Path.resolve()`.

---

## S3-совместимое хранилище (s3)

### Поддерживаемые сервисы

- AWS S3
- MinIO
- DigitalOcean Spaces
- Yandex Object Storage
- Другие S3-совместимые API

### Переменные окружения

```env
STORAGE_BACKEND=s3
S3_ACCESS_KEY_ID=<ключ>
S3_SECRET_ACCESS_KEY=<секрет>
S3_BUCKET=<имя bucket>
S3_REGION=us-east-1
# Опционально:
S3_ENDPOINT_URL=   # MinIO, DO Spaces и т.п.
S3_PUBLIC_URL=     # Базовый URL для публичного доступа
S3_PRESIGNED_EXPIRE=3600   # Срок жизни presigned URL (сек)
```

### Режимы доступа

1. **Presigned URL** (по умолчанию) — при `get_url()` возвращается временная ссылка (1 час по умолчанию). Эндпоинт `/content/media/...` делает редирект 302 на presigned URL.

2. **Публичный bucket** — при заданном `S3_PUBLIC_URL` возвращается постоянная ссылка вида `{S3_PUBLIC_URL}/{key}`.

### Настройка bucket

Рекомендуемые права IAM (минимальные):

- `s3:PutObject`
- `s3:GetObject`
- `s3:DeleteObject`
- `s3:HeadObject`

### CORS

Если фронтенд обращается к S3 напрямую (например, для предпросмотра), настройте CORS на bucket:

```json
[
  {
    "AllowedOrigins": ["https://your-domain.com"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"]
  }
]
```

---

## Миграция с local на S3

При переходе с локального хранилища на S3:

1. Создайте bucket и настройте переменные окружения.
2. Загрузите существующие файлы из `MEDIA_BASE_PATH` в S3, сохраняя структуру ключей (`images/{product_id}/{filename}`, `videos/{product_id}/{filename}`).
3. Установите `STORAGE_BACKEND=s3`.
4. Перезапустите приложение.

Скрипт миграции можно реализовать отдельно (например, `scripts/migrate_media_to_s3.py`).

---

## Docker и production

В production при `STORAGE_BACKEND=s3`:

- Не монтируйте volume для медиа (или оставьте пустым).
- Все медиа хранятся только в S3.
- Healthcheck бэкенда не зависит от доступности S3.

---

## Файлы

| Файл | Назначение |
|------|------------|
| `app/interfaces/storage.py` | Интерфейс StorageInterface |
| `app/services/media/local_storage.py` | LocalFileStorage |
| `app/services/media/s3_storage.py` | S3Storage |
| `app/services/media/factory.py` | Фабрика get_storage() |
