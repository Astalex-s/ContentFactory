# Безопасность ContentFactory

Этот документ описывает меры безопасности, реализованные в ContentFactory, и рекомендации для production deployment.

---

## Реализованные меры безопасности

### 1. Секреты в переменных окружения

**Проблема:** Хардкод паролей, ключей API, токенов в коде приводит к утечкам при публикации в Git.

**Решение:**
- Все секреты хранятся в `.env` файле
- `.env` добавлен в `.gitignore`
- `.env.example` содержит шаблон без реальных значений
- Docker Compose использует переменные окружения без дефолтных значений

**Обязательные секреты:**
```env
POSTGRES_PASSWORD=          # Пароль PostgreSQL
PGADMIN_DEFAULT_PASSWORD=   # Пароль PGAdmin
OPENAI_API_KEY=             # API ключ OpenAI
REPLICATE_API_TOKEN=        # API токен Replicate
OAUTH_SECRET_KEY=           # Fernet key для шифрования токенов
OAUTH_ENCRYPTION_SALT=      # Salt для PBKDF2
```

**Генерация ключей:**
```bash
# OAUTH_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OAUTH_ENCRYPTION_SALT
python -c "import secrets; print(secrets.token_urlsafe(16))"

# Сильный пароль
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

---

### 2. Шифрование токенов OAuth

**Проблема:** Токены OAuth хранятся в БД и могут быть украдены при компрометации БД.

**Решение:**
- Токены шифруются с помощью Fernet (PBKDF2 + AES)
- Используется PBKDF2 с 100,000 итераций для деривации ключа
- Salt для PBKDF2 хранится в переменной окружения
- Токены расшифровываются только при использовании

**Реализация:**
```python
def encrypt_token(plain: str, secret_key: str, salt: str) -> str:
    """Encrypt token with Fernet. Returns base64 string."""
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

**Файл:** `backend/app/core/encryption.py`

---

### 3. Path Traversal защита

**Проблема:** Атакующий может запросить файлы вне разрешённой директории через `../`.

**Решение:**
- Проверка resolved path относительно base path
- Использование `Path.resolve()` для нормализации пути
- Проверка, что resolved path начинается с base path

**Реализация:**
```python
@router.get("/media/{file_path:path}")
async def get_media_file(file_path: str, media: MediaStorageService = Depends(get_media_storage)):
    from pathlib import Path
    
    full_path = media.get_full_path(file_path)
    base_path = Path(get_settings().MEDIA_BASE_PATH).resolve()
    
    try:
        resolved_path = full_path.resolve()
    except (ValueError, OSError):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    if not str(resolved_path).startswith(str(base_path)):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    if not resolved_path.exists() or not resolved_path.is_file():
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    return FileResponse(path=str(resolved_path), ...)
```

**Файл:** `backend/app/routers/content.py`

---

### 4. Rate Limiting

**Проблема:** Атакующий может перегрузить AI API или вызвать большие расходы.

**Решение:**
- SlowAPI rate limiting на endpoints генерации контента
- Настраиваемые лимиты через переменные окружения
- Лимиты по IP адресу

**Реализация:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/generate/{product_id}")
@limiter.limit(get_settings().CONTENT_GENERATE_RATE_LIMIT)
async def generate_content(request: Request, ...):
    pass
```

**Лимиты:**
- Генерация контента: `10/minute` (настраивается через `CONTENT_GENERATE_RATE_LIMIT`)
- Публикация видео: `5/minute`

**Файл:** `backend/app/core/rate_limit.py`

---

### 5. Валидация входных данных

**Проблема:** Невалидные данные могут вызвать ошибки или SQL injection.

**Решение:**
- Pydantic схемы для всех входных данных
- Валидация типов, форматов, длин
- Custom validators для бизнес-правил
- Параметризованные запросы через SQLAlchemy

**Примеры:**

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

```python
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    marketplace_url: Optional[HttpUrl] = None  # Валидация URL
```

**Файлы:** `backend/app/schemas/*.py`

---

### 6. CORS

**Проблема:** Неавторизованные сайты могут делать запросы к API.

**Решение:**
- Настраиваемые разрешённые origins через `CORS_ORIGINS`
- Проверка origin на уровне FastAPI middleware

**Реализация:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Конфигурация:**
```env
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

**Файл:** `backend/app/main.py`

---

### 7. SQL Injection защита

**Проблема:** Прямые SQL запросы с конкатенацией строк уязвимы к SQL injection.

**Решение:**
- Использование SQLAlchemy ORM
- Параметризованные запросы
- Нет raw SQL в коде

**Пример:**
```python
# Безопасно (параметризованный запрос)
result = await session.execute(
    select(Product).where(Product.id == product_id)
)

# Небезопасно (не используется в проекте)
# result = await session.execute(f"SELECT * FROM products WHERE id = '{product_id}'")
```

---

### 8. Проверка владельца ресурса

**Проблема:** Пользователь может удалить чужой аккаунт.

**Решение:**
- Проверка `user_id` перед операциями
- HTTP 403 при попытке доступа к чужому ресурсу

**Реализация:**
```python
@router.delete("/accounts/{account_id}", status_code=204)
async def disconnect_account(account_id: str, oauth: OAuthService = Depends(get_oauth_service), repo: SocialAccountRepository = Depends(get_social_repo)):
    uid = oauth.get_user_id()
    acc = await repo.get_by_id(UUID(account_id))
    if not acc:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    if acc.user_id != uid:
        raise HTTPException(status_code=403, detail="Нет доступа")
    await repo.delete(acc.id)
```

**Файл:** `backend/app/routers/social.py`

---

## Рекомендации для production

### 1. HTTPS

**Обязательно** использовать HTTPS в production:

```yaml
# docker-compose.prod.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
```

**Получение SSL сертификата:**
```bash
# Let's Encrypt (бесплатно)
certbot certonly --webroot -w /var/www/html -d your-domain.com
```

---

### 2. Сильные пароли

**Требования:**
- Минимум 16 символов
- Случайная генерация
- Уникальные для каждого сервиса

**Генерация:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

---

### 3. Отключить DEBUG режим

```env
DEBUG=False
ENVIRONMENT=production
```

---

### 4. Использовать Redis для статусов задач

**Проблема:** In-memory хранилище теряется при перезапуске.

**Решение:**
```python
# backend/app/services/task_status_service.py
class TaskStatusService:
    def __init__(self, redis_client):
        self.redis = redis_client

    def set_status(self, task_id: str, status: str, ...):
        self.redis.setex(f"task:{task_id}", 3600, json.dumps({...}))
```

---

### 5. Использовать Celery для фоновых задач

**Проблема:** FastAPI BackgroundTasks не персистентны и не имеют retry.

**Решение:**
```python
# backend/app/tasks.py
@celery_app.task(bind=True, max_retries=3)
def generate_images_task(self, product_id: str):
    try:
        # Генерация изображений
        pass
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
```

---

### 6. Мониторинг и логирование

**Sentry** — для отслеживания ошибок:
```python
import sentry_sdk
sentry_sdk.init(dsn="https://...")
```

**Prometheus + Grafana** — для метрик:
```python
from prometheus_client import Counter, Histogram

request_count = Counter("http_requests_total", "Total HTTP requests")
request_duration = Histogram("http_request_duration_seconds", "HTTP request duration")
```

**ELK Stack** — для логов:
```yaml
# docker-compose.prod.yml
services:
  logstash:
    image: docker.elastic.co/logstash/logstash:8.0.0
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
```

---

### 7. Регулярно обновлять зависимости

```bash
# Проверка устаревших зависимостей
pip list --outdated

# Обновление
pip install --upgrade <package>

# Проверка уязвимостей
pip-audit
```

---

### 8. Backup БД

```bash
# Ежедневный backup PostgreSQL
docker exec contentfactory-postgres pg_dump -U contentfactory contentfactory > backup_$(date +%Y%m%d).sql

# Восстановление
docker exec -i contentfactory-postgres psql -U contentfactory contentfactory < backup_20260224.sql
```

---

### 9. Firewall

Разрешить только необходимые порты:

```bash
# ufw (Ubuntu)
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw deny 5432/tcp   # PostgreSQL (только для localhost)
ufw deny 5050/tcp   # PGAdmin (только для localhost)
ufw enable
```

---

### 10. Secrets Management

Использовать secrets management для production:

**Docker Swarm Secrets:**
```bash
echo "my_secret_password" | docker secret create postgres_password -
```

**Kubernetes Secrets:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
type: Opaque
data:
  password: <base64-encoded-password>
```

**HashiCorp Vault:**
```bash
vault kv put secret/contentfactory postgres_password=...
```

---

## Checklist для production

- [ ] Все секреты в переменных окружения
- [ ] Сильные уникальные пароли
- [ ] HTTPS настроен (Let's Encrypt)
- [ ] DEBUG=False
- [ ] CORS настроен правильно
- [ ] Rate limiting включён
- [ ] Redis для статусов задач
- [ ] Celery для фоновых задач
- [ ] Sentry для мониторинга ошибок
- [ ] Prometheus для метрик
- [ ] ELK для логов
- [ ] Регулярные backup БД
- [ ] Firewall настроен
- [ ] Secrets management (Vault/Kubernetes Secrets)
- [ ] Зависимости обновлены
- [ ] pip-audit пройден без критичных уязвимостей

---

## Контакты

При обнаружении уязвимостей создавайте private security advisory в GitHub.
