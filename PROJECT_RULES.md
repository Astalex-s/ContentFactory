📘 PROJECT RULES

AI Marketing Platform
Stack: FastAPI + PostgreSQL + React
Architecture: Clean Architecture + SOLID + Scalable + Production-Ready

1. НАЗНАЧЕНИЕ

Этот документ управляет архитектурой всего проекта на всех этапах разработки.
Любой код, добавляемый в проект, обязан соответствовать данным правилам.
PROJECT_RULES является архитектурным источником истины.

2. ГЛОБАЛЬНЫЕ ПРИНЦИПЫ

Проект строится на:
Clean Architecture
SOLID
Separation of Concerns
Dependency Injection
Низкая связанность
Высокая когезия
Расширяемость без изменения существующего кода
Production-ready mindset

Запрещено:
Хардкодить значения
Смешивать архитектурные слои
Добавлять бизнес-логику в Router
Обращаться к БД вне Repository
Вызывать внешние API напрямую из Router

3. СТРУКТУРА ПРОЕКТА
/backend
/frontend
/database
/docs
/docker
/prompts

Каждый слой должен быть изолирован и расширяем.

4. BACKEND ARCHITECTURE (FastAPI)
4.1 Структура
backend/

app/
    main.py
    core/
        config.py
        database.py
        security.py
        logging.py
    models/
    schemas/
    repositories/
    services/
        ai/
    routers/
    dependencies/
    interfaces/
    utils/

migrations/
tests/
.env
.env.example
requirements.txt
4.2 Слои
Router Layer

Только HTTP
Валидация
Вызов Service
Response schema
Без логики
Service Layer
Вся бизнес-логика
Не знает о FastAPI
Работает через интерфейсы
Repository Layer
Только работа с БД
CRUD
Без бизнес-логики
Interface Layer
Абстракции для:
AI
Соцсетей
Аналитики
Генераторов

5. DATABASE RULES (PostgreSQL)

SQLAlchemy 2.0 async
AsyncSession
UUID primary keys
Индексы по важным полям
Alembic для миграций

Запрещено:

Изменять схему вручную
Raw SQL без необходимости
Логика в моделях
Каждое изменение схемы → отдельная миграция.

6. КОНФИГУРАЦИЯ

Все секреты и параметры — только через .env.

Запрещено:
Хранить ключи в коде
Коммитить .env
Использовать:
Pydantic BaseSettings
Разделение dev/test/prod конфигураций
Строгую типизацию

7. GIT ПРАВИЛА

Обязательно использовать .gitignore.
Запрещено коммитить:
.env
node_modules
build
dist
логи
временные файлы
локальные БД
медиа

8. REACT ARCHITECTURE

Структура:
frontend/src/
app/
pages/
components/
features/
services/
hooks/
utils/
types/

Принципы:

Feature-based структура
UI отделён от логики
API вызовы только через services/
Централизованный Axios instance
Конфигурация через .env
Компонент = одна ответственность

9. API ПРАВИЛА

Backend:
Каждый endpoint имеет request/response schema
Типизация обязательна
Нельзя возвращать ORM напрямую
Пагинация обязательна
Frontend:
Нет прямых fetch в компонентах
Централизованная обработка ошибок

10. AI ARCHITECTURE

AI слой полностью изолирован.
10.1 Структура
services/ai/
    ai_service.py
    provider_factory.py
    base_provider.py
    models_registry.py
    prompt_manager.py

interfaces/
    ai_provider_interface.py
10.2 Принципы

Использовать AIProvider abstraction
Каждый провайдер — отдельная реализация
Service работает через интерфейс
Router не знает о провайдере
Провайдер не знает о FastAPI

10.3 Обязательные методы AIProvider

generate_text()
generate_image()
generate_video()
health_check()

10.4 Factory Pattern

Выбор провайдера через .env.

AI_PROVIDER=
AI_MODEL=
AI_TIMEOUT=

Без изменения кода сервиса.

10.5 Prompt Management
Промпты:

не хардкодятся
хранятся в /prompts
разделены по типу
prompts/
    text/
    image/
    video/
10.6 Fault Tolerance

AI слой обязан поддерживать:
retry
timeout
fallback модель
логирование ошибок
graceful degradation

10.7 Масштабируемость AI

AI слой должен позволять:
подключать новые модели
подключать локальные модели
batching
очереди (Redis/Celery)
вынесение в отдельный микросервис

11. СОЦСЕТИ

Каждая соцсеть реализуется как provider.
Использовать SocialProvider abstraction.
Добавление новой платформы не должно требовать изменения существующего кода.

12. АНАЛИТИКА

Аналитика отделена от генерации.
Использовать:
AnalyticsService
Метрики через отдельный слой
Расширяемость KPI

13. РАСШИРЯЕМОСТЬ

Архитектура должна позволять:
Добавлять новые AI модели
Добавлять новые типы контента
Добавлять новые маркетплейсы
Добавлять новые соцсети
Добавлять новые метрики
Без переписывания существующего кода.

Использовать:

Interfaces
Factory
Strategy
Dependency Injection

14. MCP CONTEX7

Перед добавлением любой библиотеки:
Обязательно проверить через MCP contex7:
Поддержку Python 3.11+
Совместимость с async
Актуальность релизов
Активность проекта
Без проверки библиотека не добавляется.

15. ЛОГИРОВАНИЕ

Централизованная конфигурация
Разделение уровней логирования
AI ошибки логируются отдельно
В production не возвращать stack trace

16. ТЕСТИРОВАНИЕ

Backend:
pytest
unit tests для services
тестирование repository
отдельная test DB

Frontend:
базовые тесты логики

17. БЕЗОПАСНОСТЬ
CORS конфигурируемый
HTTPS
Rate limit для AI
Подготовка под JWT
Валидация входных данных

18. ПРОИЗВОДИТЕЛЬНОСТЬ

Async everywhere
DB connection pool
Избегать N+1
Пагинация обязательна
Кэширование при необходимости

19. DOCKER

Проект обязан поддерживать Docker.
Структура:

/docker
    Dockerfile.backend
    Dockerfile.frontend
    docker-compose.yml

Backend:

Python 3.11+
non-root user
gunicorn + uvicorn workers
healthcheck
Frontend:

Production build
nginx для отдачи
Compose включает:
backend
frontend
postgres
redis
volumes
отдельную сеть

20. CI/CD

Pipeline обязан включать:
Lint
Type checking
Unit tests
Build Docker images
Security scan зависимостей
Проверку миграций
CI не должен деплоить при падающих тестах.

21. MIGRATIONS IN PRODUCTION

Миграции запускаются отдельно
Не изменять схему вручную
Проверка перед деплоем

22. HEALTH MONITORING

Backend обязан иметь:
/health
Проверку БД
Проверку AI provider
readiness и liveness

23. MEDIA

Медиа не хранить в git
Использовать volume или S3
Готовность к CDN

24. ФИНАЛЬНЫЕ ПРАВИЛА

Никакого хардкода
Никакой логики в Router
Никакого прямого доступа к БД вне Repository
Все секреты через .env
Все схемы через Pydantic
Все изменения БД через Alembic
Любая зависимость — через MCP contex7
Код должен быть масштабируемым