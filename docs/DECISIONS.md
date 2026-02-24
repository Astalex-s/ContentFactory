# Ключевые архитектурные решения

Этот документ фиксирует важные решения, принятые при разработке ContentFactory, и их обоснование.

---

## 1. Секреты и безопасность

### Решение
- Все секреты (пароли, API ключи, токены) хранятся только в переменных окружения
- Docker Compose не содержит дефолтных значений для секретов
- Токены OAuth шифруются с помощью Fernet (PBKDF2 + AES) перед сохранением в БД
- Salt для PBKDF2 хранится в отдельной переменной окружения

### Обоснование
- **Безопасность**: Хардкод секретов в коде/конфигах приводит к утечкам при публикации в Git
- **Compliance**: Соответствие best practices (12-factor app, OWASP)
- **Гибкость**: Разные секреты для dev/staging/production без изменения кода
- **Защита токенов**: Даже при компрометации БД токены OAuth остаются защищёнными

### Альтернативы
- ❌ Хардкод в коде — небезопасно
- ❌ Дефолтные значения в docker-compose.yml — небезопасно
- ❌ Хранение токенов в открытом виде — небезопасно

### Файлы
- `docker-compose.yml` — переменные без дефолтов
- `.env.example` — шаблон без реальных значений
- `backend/app/core/encryption.py` — шифрование токенов
- `backend/app/core/config.py` — настройки из .env

---

## 2. Clean Architecture

### Решение
Разделение на слои:
- **Presentation** (routers) — обработка HTTP запросов
- **Application** (services) — бизнес-логика
- **Domain** (models + repositories) — модели данных и CRUD
- **Infrastructure** (core) — конфигурация, БД, внешние API

### Обоснование
- **Тестируемость**: Легко mock зависимости для unit тестов
- **Поддерживаемость**: Чёткая ответственность каждого слоя
- **Масштабируемость**: Легко добавлять новые фичи без изменения существующего кода
- **Независимость**: Бизнес-логика не зависит от FastAPI, БД, внешних API

### Альтернативы
- ❌ Монолит (всё в роутерах) — сложно тестировать и поддерживать
- ❌ Анемичная модель (логика в роутерах) — нарушение SRP

### Файлы
- `backend/app/routers/` — Presentation
- `backend/app/services/` — Application
- `backend/app/models/`, `backend/app/repositories/` — Domain
- `backend/app/core/` — Infrastructure

---

## 3. Асинхронность (async/await)

### Решение
Полностью асинхронное приложение:
- FastAPI async endpoints
- SQLAlchemy async engine/session
- httpx для HTTP запросов
- asyncio для параллельных операций

### Обоснование
- **Производительность**: Высокая пропускная способность при I/O операциях
- **Масштабируемость**: Один процесс может обрабатывать тысячи запросов
- **Современность**: Async/await — стандарт для Python 3.12+
- **AI API**: Долгие запросы к AI не блокируют другие запросы

### Альтернативы
- ❌ Синхронный код — низкая производительность при I/O
- ❌ Threading — сложнее в отладке, GIL ограничивает производительность
- ❌ Multiprocessing — больше потребление памяти

### Файлы
- `backend/app/main.py` — async FastAPI app
- `backend/app/core/database.py` — async SQLAlchemy
- `backend/app/services/` — async сервисы

---

## 4. Фоновые задачи (MVP: BackgroundTasks)

### Решение
Для генерации изображений и видео используется FastAPI `BackgroundTasks`.

### Обоснование
- **Простота**: Не требует дополнительных сервисов (Redis, Celery)
- **MVP**: Достаточно для прототипа и малой нагрузки
- **Быстрый старт**: Работает из коробки

### Ограничения
- Работает только в одном процессе
- Нет персистентности (теряются при перезапуске)
- Нет retry механизма
- Нет распределённой обработки

### Production рекомендация
Использовать **Celery + Redis**:
- Персистентность задач
- Retry при ошибках
- Распределённая обработка
- Мониторинг (Flower)

### Файлы
- `backend/app/routers/content.py` — BackgroundTasks для генерации
- `backend/app/services/task_status_service.py` — in-memory статусы

---

## 5. Хранение статусов задач (MVP: in-memory)

### Решение
Статусы фоновых задач хранятся в памяти через `TaskStatusService`.

### Обоснование
- **Простота**: Не требует Redis
- **MVP**: Достаточно для прототипа
- **Быстрый доступ**: O(1) lookup

### Ограничения
- Теряются при перезапуске
- Не работает при горизонтальном масштабировании

### Production рекомендация
Использовать **Redis**:
```python
class TaskStatusService:
    def __init__(self, redis_client):
        self.redis = redis_client

    def set_status(self, task_id: str, status: str, ...):
        self.redis.setex(f"task:{task_id}", 3600, json.dumps({...}))
```

### Файлы
- `backend/app/services/task_status_service.py`

---

## 6. OAuth и публикация в соцсети

### Решение
- OAuth 2.0 Authorization Code Flow для YouTube, VK, Rutube
- Токены шифруются перед сохранением в БД
- Поддержка нескольких YouTube каналов через `channel_id`
- Автоматический refresh токенов при истечении
- QR-код с ссылкой на товар в конце видео
- Ссылка в описании только для длинных видео (≥60 сек)

### Обоснование
- **Безопасность**: Токены защищены шифрованием
- **Удобство**: Пользователь может подключить несколько каналов
- **Автоматизация**: Refresh токенов без участия пользователя
- **Маркетинг**: QR-код увеличивает конверсию (особенно для Shorts)
- **UX**: Ссылка в описании не нужна для Shorts (не кликабельна)

### Альтернативы
- ❌ API ключи вместо OAuth — нет доступа к пользовательским ресурсам
- ❌ Хранение токенов в открытом виде — небезопасно
- ❌ Один канал на пользователя — ограничивает функционал

### Файлы
- `backend/app/services/social/oauth_service.py` — OAuth flow
- `backend/app/services/social/youtube_provider.py` — YouTube upload
- `backend/app/services/video/video_overlay.py` — QR-код overlay
- `backend/app/services/publication_service.py` — логика публикации

---

## 7. Валидация и типизация

### Решение
- Pydantic схемы для всех входных/выходных данных
- Полная типизация (Python 3.12+)
- Custom validators для бизнес-правил
- Enum для ограниченных значений

### Обоснование
- **Безопасность**: Защита от невалидных данных
- **Документация**: Автоматическая генерация OpenAPI схемы
- **Разработка**: IDE подсказки и проверка типов
- **Качество**: Ошибки типов обнаруживаются на этапе разработки

### Примеры
```python
class PublishRequest(BaseModel):
    platform: str = Field(..., pattern="^(youtube|vk|rutube)$")
    scheduled_at: datetime | None = None
    
    @field_validator("scheduled_at")
    @classmethod
    def validate_future_time(cls, v: datetime | None) -> datetime | None:
        if v is not None and v < datetime.now(timezone.utc):
            raise ValueError("scheduled_at должно быть в будущем")
        return v
```

### Файлы
- `backend/app/schemas/` — Pydantic схемы

---

## 8. Rate Limiting

### Решение
SlowAPI для защиты от перегрузки AI API:
- Генерация контента: 10 запросов/минуту
- Публикация видео: 5 запросов/минуту

### Обоснование
- **Защита от злоупотреблений**: Предотвращение DDoS и спама
- **Контроль расходов**: AI API стоят дорого
- **Стабильность**: Предотвращение перегрузки сервера

### Альтернативы
- ❌ Без rate limiting — риск больших расходов и перегрузки
- ✅ Redis-based rate limiting — для production (распределённый)

### Файлы
- `backend/app/core/rate_limit.py`
- `backend/app/routers/content.py` — применение лимитов

---

## 9. Path Traversal защита

### Решение
Проверка resolved path при отдаче медиафайлов:
```python
resolved_path = full_path.resolve()
if not str(resolved_path).startswith(str(base_path)):
    raise HTTPException(status_code=400, detail="Invalid path")
```

### Обоснование
- **Безопасность**: Защита от доступа к файлам вне MEDIA_BASE_PATH
- **Compliance**: Соответствие OWASP Top 10

### Альтернативы
- ❌ Проверка только на `..` — недостаточно (symlinks, URL encoding)
- ❌ Без проверки — критическая уязвимость

### Файлы
- `backend/app/routers/content.py` — endpoint `/media/{file_path:path}`

---

## 10. Миграции БД (Alembic)

### Решение
Все изменения схемы БД через Alembic миграции.

### Обоснование
- **Версионирование**: История изменений схемы
- **Откат**: Возможность rollback при проблемах
- **Воспроизводимость**: Одинаковая схема на dev/staging/production
- **Командная работа**: Избежание конфликтов при изменении схемы

### Правила
- Миграции идемпотентные
- Миграции не содержат данных (только DDL)
- Миграции имеют `upgrade()` и `downgrade()`
- Миграции тестируются перед применением

### Файлы
- `backend/migrations/versions/` — миграции
- `backend/alembic.ini` — конфигурация Alembic

---

## Итоги

Все решения направлены на:
- **Безопасность** — защита секретов, токенов, данных
- **Масштабируемость** — async, Clean Architecture, фоновые задачи
- **Поддерживаемость** — типизация, валидация, чёткая структура
- **Качество** — тестируемость, документация, best practices

Для production рекомендуется:
- Celery + Redis вместо BackgroundTasks
- Redis для статусов задач
- Secrets management (Vault/Kubernetes Secrets)
- Мониторинг (Sentry, Prometheus, ELK)
- HTTPS (Let's Encrypt)
