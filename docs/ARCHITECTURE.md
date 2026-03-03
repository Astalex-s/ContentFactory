# Архитектура ContentFactory

Этот документ описывает архитектуру приложения ContentFactory, принципы проектирования и ключевые решения.

---

## Общая архитектура

ContentFactory следует принципам **Clean Architecture** с чёткимразделением ответственности между слоями:

```
┌─────────────────────────────────────────────────────┐
│                   Presentation                       │
│              (FastAPI Routers + React)              │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│                 Application                          │
│              (Services + Use Cases)                  │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│                   Domain                             │
│            (Models + Business Logic)                 │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│                Infrastructure                        │
│        (Database + External APIs + Storage)          │
└─────────────────────────────────────────────────────┘
```

---

## Backend архитектура

### Структура слоёв

#### 1. Presentation Layer (Routers)

**Расположение:** `backend/app/routers/`

**Ответственность:**
- Обработка HTTP запросов
- Валидация входных данных (Pydantic)
- Вызов сервисов через dependency injection
- Формирование HTTP ответов
- Rate limiting

**Файлы:**
- `health.py` — healthcheck endpoints
- `products.py` — CRUD товаров
- `content.py` — генерация контента
- `tasks.py` — статусы фоновых задач
- `social.py` — OAuth подключение
- `publish.py` — публикация в соцсети
- `analytics.py` — метрики, AI-рекомендации, обновление статистики из соцсетей

**Правила:**
- Роуты НЕ содержат бизнес-логику
- Роуты НЕ работают с БД напрямую
- Все зависимости через FastAPI Depends()
- Все ошибки возвращаются как HTTPException

#### 2. Application Layer (Services)

**Расположение:** `backend/app/services/`

**Ответственность:**
- Бизнес-логика приложения
- Оркестрация между репозиториями
- Вызов внешних API (AI, социальные сети)
- Обработка файлов и медиа

**Структура:**

```
services/
├── ai/                         # AI провайдеры
│   ├── openai_provider.py     # OpenAI API клиент
│   └── prompt_builder.py      # Промпты: build_single_image_prompt, build_product_prompt
├── image/                      # Генерация изображений
│   ├── image_generation_service.py
│   └── replicate_provider.py
├── video/                      # Генерация видео
│   ├── video_generation_service.py
│   └── video_overlay.py       # QR-код overlay
├── social/                     # OAuth и публикация
│   ├── oauth_service.py       # OAuth flow
│   ├── base_provider.py       # Базовый класс провайдера
│   ├── youtube_provider.py    # YouTube upload
│   └── social_factory.py      # Factory pattern
├── media/
│   ├── local_storage.py       # Локальное хранение файлов
│   ├── s3_storage.py          # S3-совместимое хранение
│   └── factory.py             # Фабрика get_storage()
├── product.py                  # ProductService
├── content_service.py          # ContentService
├── text_generation_service.py  # Генерация текста
├── marketplace_import.py       # Импорт товаров
├── publication_service.py      # Публикация видео
├── task_status_service.py      # Статусы задач (in-memory, asyncio.Lock)
└── status_sync_service.py      # Синхронизация статусов
```

**Правила:**
- Сервисы НЕ знают о FastAPI (Request, Response и т.д.)
- Сервисы работают с репозиториями через dependency injection
- Сервисы возвращают domain модели или DTO
- Сервисы выбрасывают ValueError для бизнес-ошибок

#### 3. Domain Layer (Models + Repositories)

**Расположение:** `backend/app/models/`, `backend/app/repositories/`

**Ответственность:**
- Определение моделей данных (SQLAlchemy)
- CRUD операции (репозитории)
- Бизнес-правила на уровне модели

**Модели:**
- `Product` — товары маркетплейса
- `GeneratedContent` — сгенерированный контент (текст, изображения, видео)
- `SocialAccount` — OAuth-подключённые аккаунты соцсетей
- `PublicationQueue` — очередь публикаций в соцсети
- `ContentMetrics` — метрики аналитики (просмотры, клики, CTR)
- `OAuthAppCredentials` — учётные данные OAuth-приложений (client_id, client_secret зашифрованы)

**Репозитории:**
- `ProductRepository` — CRUD товаров
- `GeneratedContentRepository` — CRUD контента
- `SocialAccountRepository` — CRUD аккаунтов
- `PublicationQueueRepository` — CRUD публикаций
- `ContentMetricsRepository` — CRUD метрик аналитики
- `OAuthAppCredentialsRepository` — CRUD OAuth-приложений

**Правила:**
- Репозитории НЕ содержат бизнес-логику
- Репозитории работают только с одной моделью
- Репозитории возвращают модели SQLAlchemy
- Все запросы асинхронные (async/await)

#### 4. Infrastructure Layer

**Расположение:** `backend/app/core/`

**Ответственность:**
- Конфигурация приложения
- Подключение к БД
- Логирование
- Шифрование
- Rate limiting

**Файлы:**
- `config.py` — настройки из .env (Pydantic Settings)
- `database.py` — SQLAlchemy engine/session
- `encryption.py` — Fernet шифрование токенов
- `logging.py` — настройка логирования
- `rate_limit.py` — SlowAPI rate limiting

---

## Ключевые паттерны

### 1. Dependency Injection

Все зависимости передаются через FastAPI `Depends()`:

```python
@router.get("/products/{product_id}")
async def get_product(
    product_id: UUID,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    product = await service.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return product
```

**Преимущества:**
- Легко тестировать (mock зависимости)
- Явные зависимости
- Переиспользование кода

### 2. Repository Pattern

Весь доступ к БД через репозитории:

```python
class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, product_id: UUID) -> Product | None:
        result = await self.session.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()
```

**Преимущества:**
- Изоляция SQL от бизнес-логики
- Легко менять БД
- Переиспользование запросов

### 3. Service Layer

Бизнес-логика в сервисах:

```python
class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    async def get_by_id(self, product_id: UUID) -> Product | None:
        return await self.repository.get_by_id(product_id)

    async def delete(self, product_id: UUID) -> bool:
        product = await self.repository.get_by_id(product_id)
        if not product:
            return False
        await self.repository.delete(product_id)
        return True
```

**Преимущества:**
- Переиспользование бизнес-логики
- Легко тестировать
- Чёткая ответственность

### 4. Factory Pattern

Для создания провайдеров социальных сетей:

```python
def get_provider(platform: SocialPlatform) -> BaseSocialProvider:
    if platform == SocialPlatform.YOUTUBE:
        return YouTubeProvider()
    raise ValueError(f"Unsupported platform: {platform}")
```

**Преимущества:**
- Легко добавлять новые платформы
- Единый интерфейс для всех провайдеров
- Изоляция логики платформ

### 5. Strategy Pattern

Для AI провайдеров (OpenAI, Replicate):

```python
class BaseAIProvider(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        pass

class OpenAIProvider(BaseAIProvider):
    async def generate_text(self, prompt: str) -> str:
        # OpenAI API call
        pass
```

**Преимущества:**
- Легко менять AI провайдера
- Единый интерфейс
- Изоляция логики провайдера

---

## Асинхронность

Всё приложение полностью асинхронное:

- **FastAPI** — async endpoints
- **SQLAlchemy** — async engine/session
- **httpx** — async HTTP клиент
- **asyncio** — для параллельных операций

**Пример:**

```python
async def generate_images_for_product(
    self,
    product_id: UUID,
    count: int = 1,
) -> list[GeneratedContent]:
    product = await self.product_repo.get_by_id(product_id)
    if not product:
        raise ValueError("Product not found")

    # Генерация 1 изображения (GPT промпт + Replicate image-to-image)
    content = await self._generate_single_image(product)
    return [content]
```

---

## Фоновые задачи

### MVP: FastAPI BackgroundTasks

Для генерации изображений и видео используется `BackgroundTasks`:

```python
@router.post("/images/{product_id}")
async def generate_images(
    product_id: UUID,
    background_tasks: BackgroundTasks,
) -> TaskResponse:
    task_id = str(uuid.uuid4())
    task_svc = get_task_status_service()
    await task_svc.set_status(task_id, "pending")
    background_tasks.add_task(_run_image_generation, task_id, product_id)
    return TaskResponse(task_id=task_id, status="pending")
```

**Ограничения:**
- Работает только в одном процессе
- Нет персистентности (при перезапуске теряются)
- Нет retry механизма

### Production: Celery (рекомендуется)

Для production рекомендуется использовать Celery + Redis:

```python
@celery_app.task(bind=True, max_retries=3)
def generate_images_task(self, product_id: str):
    try:
        # Генерация изображений
        pass
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
```

---

## Безопасность

### 1. Шифрование токенов OAuth

Токены шифруются с помощью Fernet (PBKDF2 + AES):

```python
def encrypt_token(plain: str, secret_key: str, salt: str) -> str:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt.encode(),
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
    f = Fernet(key)
    return f.encrypt(plain.encode()).decode()
```

**Требования:**
- `OAUTH_SECRET_KEY` — Fernet key (base64, 32 байта)
- `OAUTH_ENCRYPTION_SALT` — salt для PBKDF2 (случайная строка)

### 2. Path Traversal защита

При отдаче медиафайлов проверяется путь:

```python
full_path = media.get_full_path(file_path)
base_path = Path(settings.MEDIA_BASE_PATH).resolve()
resolved_path = full_path.resolve()

if not str(resolved_path).startswith(str(base_path)):
    raise HTTPException(status_code=400, detail="Invalid path")
```

### 3. Rate Limiting

Защита от перегрузки AI API:

```python
@router.post("/generate/{product_id}")
@limiter.limit(settings.CONTENT_GENERATE_RATE_LIMIT)
async def generate_content(request: Request, ...):
    pass
```

### 4. Валидация входных данных

Все входные данные валидируются через Pydantic:

```python
class PublishRequest(BaseModel):
    platform: str = Field(..., pattern="^youtube$")
    account_id: UUID
    scheduled_at: datetime | None = None
    title: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=5000)

    @field_validator("scheduled_at")
    @classmethod
    def validate_future_time(cls, v: datetime | None) -> datetime | None:
        if v is not None and v < datetime.now(timezone.utc):
            raise ValueError("scheduled_at должно быть в будущем")
        return v
```

---

## База данных

### Миграции

Используется Alembic для версионирования схемы БД:

```bash
# Создание новой миграции
alembic revision -m "add_new_column"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1
```

**Правила:**
- Миграции идемпотентные
- Миграции не содержат данных (только DDL)
- Миграции имеют `upgrade()` и `downgrade()`

### Индексы

Для оптимизации запросов используются индексы:

```python
class Product(Base):
    __tablename__ = "products"
    
    category: Mapped[Optional[str]] = mapped_column(
        String(255),
        index=True,  # Индекс для фильтрации
    )
    price: Mapped[Optional[float]] = mapped_column(
        Float,
        index=True,  # Индекс для сортировки
    )
```

### Связи

Используются Foreign Keys с CASCADE:

```python
class GeneratedContent(Base):
    __tablename__ = "generated_content"
    
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
    )
```

---

## Frontend архитектура

### Feature-based структура

```
frontend/src/
├── features/
│   ├── content/           # Генерация контента
│   │   ├── api.ts        # API клиент
│   │   ├── types.ts      # TypeScript типы
│   │   └── hooks.ts      # React hooks
│   └── social/           # OAuth и публикация
│       ├── api.ts
│       ├── types.ts
│       ├── hooks.ts
│       └── components/   # React компоненты
├── pages/                # Страницы
├── services/             # Общие сервисы
└── App.tsx
```

### API клиенты

Все API вызовы через axios:

```typescript
export const contentApi = {
  async generateText(productId: string, request: GenerateContentRequest) {
    const { data } = await api.post(
      `/content/generate/${productId}`,
      request
    );
    return data;
  },
};
```

### React Hooks

Переиспользуемая логика в hooks:

```typescript
export function useSocialAccounts() {
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchAccounts = async () => {
    setLoading(true);
    try {
      const data = await socialApi.listAccounts();
      setAccounts(data.accounts);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  return { accounts, loading, refetch: fetchAccounts };
}
```

---

## Масштабирование

### Текущие ограничения (MVP)

1. **Фоновые задачи** — FastAPI BackgroundTasks (single process)
2. **Статусы задач** — in-memory (теряются при перезапуске)
3. **Сессии** — нет (MVP: один пользователь)
4. **Кеширование** — нет

### Рекомендации для production

1. **Celery + Redis** — для фоновых задач
2. **Redis** — для кеширования и статусов задач
3. **JWT** — для аутентификации пользователей
4. **CDN** — для отдачи медиафайлов
5. **Load Balancer** — для горизонтального масштабирования
6. **Monitoring** — Sentry, Prometheus, Grafana
7. **Logging** — ELK stack (Elasticsearch, Logstash, Kibana)

---

## Тестирование

### Unit тесты

Тестирование сервисов с mock репозиториями:

```python
@pytest.mark.asyncio
async def test_product_service_get_by_id():
    # Arrange
    mock_repo = MagicMock(ProductRepository)
    mock_repo.get_by_id.return_value = Product(id=uuid4(), name="Test")
    service = ProductService(mock_repo)
    
    # Act
    product = await service.get_by_id(uuid4())
    
    # Assert
    assert product is not None
    assert product.name == "Test"
```

### Integration тесты

Тестирование API endpoints:

```python
@pytest.mark.asyncio
async def test_get_product(client: AsyncClient):
    # Arrange
    product_id = await create_test_product()
    
    # Act
    response = await client.get(f"/products/{product_id}")
    
    # Assert
    assert response.status_code == 200
    assert response.json()["name"] == "Test Product"
```

---

## Мониторинг и логирование

### Логирование

Все логи пишутся в stdout/stderr (12-factor):

```python
import logging

log = logging.getLogger(__name__)

log.info("Product created: %s", product.id)
log.warning("Token refresh failed: %s", error)
log.error("Video generation failed: %s", error, exc_info=True)
```

### Healthcheck

Endpoints для проверки здоровья:

- `GET /health` — проверка работы приложения
- `GET /health/db` — проверка подключения к БД

---

## Заключение

ContentFactory следует современным best practices:

- Clean Architecture
- Dependency Injection
- Repository Pattern
- Async/await
- Type Safety
- Security First
- 12-factor App

Это обеспечивает:
- Легкость тестирования
- Масштабируемость
- Поддерживаемость
- Безопасность
