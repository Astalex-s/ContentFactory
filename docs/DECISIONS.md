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
- OAuth 2.0 Authorization Code Flow для YouTube и VK
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
    platform: str = Field(..., pattern="^(youtube|vk)$")
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

## 11. Хранение медиа (S3 для production)

### Решение
- Абстракция `StorageInterface` с реализациями `LocalFileStorage` (dev) и `S3Storage` (production)
- Переключение через `STORAGE_BACKEND=local|s3`
- Секреты S3 только в .env
- Для S3: presigned URL или публичный bucket

### Обоснование
- **Масштабируемость**: S3 не ограничен диском сервера
- **Production-ready**: Готовность к деплою без volume для медиа
- **Гибкость**: Замена бэкенда без изменения сервисов (DI, интерфейс)
- **Совместимость**: MinIO, DigitalOcean Spaces, Yandex Object Storage

### Альтернативы
- ❌ Только локальная FS — не масштабируется, теряется при пересоздании контейнера
- ✅ CDN перед S3 — для ускорения отдачи в production

### Файлы
- `app/interfaces/storage.py` — интерфейс
- `app/services/media/local_storage.py`, `s3_storage.py` — реализации
- `docs/STORAGE.md` — документация

---

## 12. OAuth-приложения в БД (а не в .env)

### Решение
Учётные данные OAuth-приложений (client_id, client_secret для YouTube/VK) хранятся
**только в БД** в зашифрованном виде (таблица `oauth_app_credentials`). В `.env` — только
ключи шифрования (`OAUTH_SECRET_KEY`, `OAUTH_ENCRYPTION_SALT`).

### Обоснование
- **Гибкость**: пользователь может добавлять и менять OAuth-приложения через UI без перезапуска
- **Масштабируемость**: поддержка нескольких приложений на одну платформу
- **Безопасность**: client_secret зашифрован, не отображается в API и логах
- **Удобство**: не нужно редактировать `.env` и перезапускать контейнер

### Альтернативы
- ❌ client_id/client_secret в .env — негибко, требует перезапуска при смене
- ❌ Хранение в открытом виде в БД — небезопасно

### Файлы
- `backend/app/models/oauth_app_credentials.py` — модель
- `backend/app/repositories/oauth_app_credentials.py` — репозиторий
- `backend/app/services/social/oauth_service.py` — использование при OAuth flow

---

## 13. Автозапуск контейнеров при деплое и перезагрузке

### Решение
- **restart: always** в docker-compose.prod.yml — контейнеры всегда перезапускаются при падении
- **systemd** — unit `contentfactory.service` для автозапуска при загрузке сервера (основной способ)
- **cron @reboot** — резервный способ: при загрузке сервера через 45 секунд выполняется `docker compose up -d` (если systemd недоступен или не сработал)
- **stop вместо down** при деплое — не останавливать контейнеры без последующего `up -d`, иначе они останутся остановленными
- **Попытка sudo** — если deploy-пользователь не может писать в `/etc/systemd/system`, используется `sudo` для установки systemd unit

### Обоснование
- **Надёжность**: Двойная защита (systemd + cron @reboot) гарантирует запуск после перезагрузки
- **Безопасность**: `down` без последующего `up -d` оставляет сервисы остановленными — риск 502
- **Гибкость**: deploy-пользователь без root может развернуть приложение; systemd устанавливается через sudo при наличии прав
- **Устойчивость**: `restart: always` — контейнеры восстанавливаются при сбоях

### Альтернативы
- ❌ Только systemd — при проблемах с systemd контейнеры не запустятся
- ❌ `down` перед pull — риск оставить контейнеры остановленными при сбое деплоя
- ❌ `restart: unless-stopped` — при ручной остановке контейнеры не перезапустятся

### Файлы
- `docker-compose.prod.yml` — restart: always
- `deploy/contentfactory.service` — systemd unit
- `.github/workflows/deploy.yml` — cron @reboot, stop вместо down, sudo для systemd

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
