# CI/CD — Непрерывная интеграция и доставка

## Содержание

- [Обзор](#обзор)
- [GitHub Actions Workflows](#github-actions-workflows)
  - [CI Workflow (ci.yml)](#ci-workflow-ciyml)
  - [Build Workflow (build.yml)](#build-workflow-buildyml)
  - [Deploy Workflow (deploy.yml)](#deploy-workflow-deployyml)
- [GitHub Secrets и переменные](#github-secrets-и-переменные)
- [Настройка сервера](#настройка-сервера)
- [Структура файлов на сервере](#структура-файлов-на-сервере)
- [Первое развёртывание](#первое-развёртывание)
- [Локальные скрипты проверки](#локальные-скрипты-проверки)
- [Troubleshooting](#troubleshooting)

---

## Обзор

ContentFactory использует GitHub Actions для автоматизации CI/CD процессов:

- **Continuous Integration (CI):** автоматическая проверка кода при каждом push и pull request
- **Build:** сборка и публикация Docker-образов в GitHub Container Registry
- **Deploy:** автоматический деплой на сервер после успешной сборки

**Принципы:**

- Все секреты только через GitHub Secrets
- Деплой только при зелёном CI (все тесты прошли)
- Никаких хардкоженных паролей и ключей в коде
- CI — источник истины для качества кода

---

## GitHub Actions Workflows

### CI Workflow (ci.yml)

**Файл:** `.github/workflows/ci.yml`

**Триггеры:**
- Push в ветки: `main`, `develop`, `feature/**`
- Pull requests в ветки: `main`, `develop`

**Jobs:**

#### 1. backend-lint
Проверка форматирования и линтинг backend-кода.

**Шаги:**
- Установка Python 3.12
- Установка зависимостей из `backend/requirements.txt`
- Запуск **Black** (format check): `black --check app/ tests/`
- Запуск **Ruff** (lint): `ruff check app/ tests/`

**Результат:** Job падает при нарушении стиля кода.

#### 2. backend-typecheck
Проверка типов в backend-коде.

**Шаги:**
- Установка Python 3.12
- Установка зависимостей
- Запуск **Pyright**: `pyright app/`

**Результат:** Job падает при ошибках типизации.

#### 3. backend-test
Запуск unit и integration тестов backend.

**Зависимости:** `backend-lint`, `backend-typecheck`

**Инфраструктура:**
- PostgreSQL 16 (контейнер в GitHub Actions)
- Тестовая база данных: `test_contentfactory`

**Переменные окружения:**
```bash
DATABASE_URL=postgresql+asyncpg://test_user:test_password@localhost:5432/test_contentfactory
OPENAI_API_KEY=test_key_placeholder
REPLICATE_API_TOKEN=test_token_placeholder
OAUTH_SECRET_KEY=test_secret_key_for_ci_only
OAUTH_ENCRYPTION_SALT=test_salt_for_ci_only
STORAGE_BACKEND=local
MEDIA_BASE_PATH=./media
```

**Шаги:**
- Установка Python 3.12 и зависимостей
- Установка pytest, pytest-asyncio, pytest-cov
- Запуск тестов: `pytest tests/ -v --tb=short --cov=app --cov-report=term-missing`
- Загрузка coverage отчёта (опционально)

**Результат:** Job падает при падении хотя бы одного теста.

#### 4. backend-migrations
Проверка корректности миграций Alembic.

**Зависимости:** `backend-lint`

**Инфраструктура:**
- PostgreSQL 16 (контейнер)
- Тестовая база данных: `test_migrations`

**Шаги:**
- Установка Python 3.12 и зависимостей
- Запуск миграций: `alembic upgrade head`
- Проверка статуса: `alembic current`

**Результат:** Job падает при ошибках применения миграций.

#### 5. frontend-lint
Проверка линтинга и типов frontend-кода.

**Шаги:**
- Установка Node.js 20
- Установка зависимостей: `npm ci`
- Запуск ESLint: `npm run lint`
- Проверка TypeScript: `npx tsc --noEmit`

**Результат:** Job падает при ошибках линтинга или типизации.

#### 6. frontend-build
Проверка сборки frontend.

**Зависимости:** `frontend-lint`

**Шаги:**
- Установка Node.js 20 и зависимостей
- Сборка: `npm run build`

**Переменные окружения:**
```bash
VITE_API_BASE_URL=http://localhost:8000
```

**Результат:** Job падает при ошибках сборки.

#### 7. ci-success
Финальная проверка всех jobs.

**Зависимости:** `backend-test`, `backend-migrations`, `frontend-build`

**Результат:** Job падает, если хотя бы один из зависимых jobs не успешен.

---

### Build Workflow (build.yml)

**Файл:** `.github/workflows/build.yml`

**Триггеры:**
- Push в ветки: `main`, `develop`
- Push тегов: `v*`
- Успешное завершение CI workflow для ветки `main`

**Permissions:**
- `contents: read`
- `packages: write`

**Jobs:**

#### 1. check-ci
Проверка статуса CI workflow (только для workflow_run триггера).

**Результат:** Job падает, если CI не прошёл успешно.

#### 2. build-backend
Сборка и публикация Docker-образа backend.

**Шаги:**
- Checkout кода
- Настройка Docker Buildx
- Логин в GitHub Container Registry (ghcr.io)
- Извлечение метаданных (теги, labels)
- Сборка и push образа

**Теги образа:**
- `ghcr.io/<owner>/contentfactory-backend:main` (для ветки main)
- `ghcr.io/<owner>/contentfactory-backend:develop` (для ветки develop)
- `ghcr.io/<owner>/contentfactory-backend:v1.0.0` (для тега v1.0.0)
- `ghcr.io/<owner>/contentfactory-backend:latest` (для main)

**Контекст:** `./backend`
**Dockerfile:** `./backend/Dockerfile`
**Платформа:** `linux/amd64`

#### 3. build-frontend
Сборка и публикация Docker-образа frontend.

**Аналогично build-backend**, но:
- **Контекст:** `./frontend`
- **Dockerfile:** `./frontend/Dockerfile`
- **Build-args:** `VITE_API_BASE_URL` (из переменных или default)

**Теги образа:**
- `ghcr.io/<owner>/contentfactory-frontend:main`
- `ghcr.io/<owner>/contentfactory-frontend:develop`
- `ghcr.io/<owner>/contentfactory-frontend:v1.0.0`
- `ghcr.io/<owner>/contentfactory-frontend:latest`

#### 4. build-success
Финальная проверка всех build jobs.

**Зависимости:** `build-backend`, `build-frontend`

**Результат:** Job падает, если хотя бы одна сборка не успешна.

---

### Deploy Workflow (deploy.yml)

**Файл:** `.github/workflows/deploy.yml`

**Триггеры:**
- **Ручной запуск** (workflow_dispatch) с выбором окружения (production/staging)
- Push тегов: `v*`
- Успешное завершение Build workflow для ветки `main`

**Permissions:**
- `contents: read`

**Jobs:**

#### 1. check-build
Проверка статуса Build workflow (только для workflow_run триггера).

**Результат:** Job падает, если Build не прошёл успешно.

#### 2. deploy
Деплой на сервер по SSH.

**Environment:** `production` или `staging` (из inputs)

**Шаги:**

1. **Checkout кода**
2. **Настройка SSH ключа:**
   - Создание `~/.ssh/deploy_key` из секрета `SSH_PRIVATE_KEY`
   - Добавление хоста в `known_hosts`
3. **Деплой на сервер:**
   - Подключение по SSH
   - Переход в директорию деплоя (`DEPLOY_PATH`)
   - `git pull` (обновление кода)
   - `docker compose pull` (загрузка новых образов при работающих контейнерах; **без stop/down**)
   - `docker compose up -d postgres` (запуск postgres для миграций)
   - Ожидание готовности Postgres
   - `docker compose run --rm backend alembic upgrade head` (миграции)
   - `docker compose up -d --force-recreate` (запуск всех сервисов с новыми образами)
   - Проверка, что backend и frontend в статусе Up (при необходимости — повторный `up -d`)
   - `docker image prune`, `docker builder prune` (освобождение места)
   - Установка systemd (с попыткой sudo при отсутствии прав)
   - Установка cron (process-pending, auto-publish-check, @reboot)
   - Проверка статуса сервисов
4. **Cleanup SSH ключа** (всегда выполняется)
5. **Проверка деплоя:**
   - Статус контейнеров
   - Логи backend
   - Health check

**Используемые секреты:**
- `SSH_HOST` — хост сервера
- `SSH_USER` — пользователь для SSH
- `SSH_PRIVATE_KEY` — приватный SSH-ключ
- `SSH_PORT` — порт SSH (по умолчанию 22)
- `DEPLOY_PATH` — путь к приложению на сервере

#### 3. deploy-notification
Уведомление о результате деплоя.

**Зависимости:** `deploy`

**Результат:** Выводит статус деплоя (успех/ошибка).

---

## GitHub Secrets и переменные

Все секреты настраиваются в: **GitHub Repository → Settings → Secrets and variables → Actions**

### Для CI (тесты)

| Secret / Variable | Назначение | Обязательность |
|-------------------|------------|----------------|
| `DATABASE_URL` | URL тестовой PostgreSQL для pytest | Опционально (если используется сервис postgres в CI) |
| `OPENAI_API_KEY` | Для тестов, вызывающих OpenAI | Опционально (можно заглушка) |
| `REPLICATE_API_TOKEN` | Для тестов Replicate | Опционально (можно заглушка) |

**Примечание:** В текущей конфигурации CI использует сервис PostgreSQL в workflow, поэтому `DATABASE_URL` формируется автоматически. Тестовые ключи API — заглушки, чтобы не падали импорты.

### Для сборки образов

| Secret / Variable | Назначение | Обязательность |
|-------------------|------------|----------------|
| `GITHUB_TOKEN` | Встроенный токен для push в ghcr.io | Автоматически доступен |

### Для деплоя на сервер

| Secret / Variable | Назначение | Обязательность | Пример значения |
|-------------------|------------|----------------|-----------------|
| `SSH_HOST` | Хост сервера (IP или домен) | **Да** | `203.0.113.10` или `example.com` |
| `SSH_USER` | Пользователь для SSH | **Да** | `deploy` |
| `SSH_PRIVATE_KEY` | Приватный SSH-ключ (содержимое файла) | **Да** | `-----BEGIN OPENSSH PRIVATE KEY-----\n...` |
| `SSH_PORT` | Порт SSH | Опционально | `22` (по умолчанию) |
| `DEPLOY_PATH` | Абсолютный путь к приложению на сервере | **Да** | `/var/www/contentfactory` |

### Для S3-хранилища (production, опционально)

При использовании `STORAGE_BACKEND=s3` добавьте в GitHub Secrets — deploy-шаг автоматически подставит их в `.env` на сервере:

| Secret | Назначение | Обязательность |
|--------|------------|----------------|
| `S3_ACCESS_KEY_ID` | Ключ доступа S3 | При S3 (вместе с S3_BUCKET) |
| `S3_SECRET_ACCESS_KEY` | Секретный ключ S3 | При S3 |
| `S3_BUCKET` | Имя bucket | При S3 |
| `S3_REGION` | Регион (например us-east-1) | Опционально |
| `S3_ENDPOINT_URL` | URL эндпоинта (MinIO, DO Spaces) | Опционально |
| `S3_PUBLIC_URL` | Базовый URL для публичного доступа | Опционально |
| `S3_PRESIGNED_EXPIRE` | Срок жизни presigned URL (сек) | Опционально |

**Логика:** если заданы `S3_ACCESS_KEY_ID` и `S3_BUCKET`, deploy при каждом запуске обновляет в `.env` блок S3 (удаляет старые `STORAGE_BACKEND` и `S3_*`, добавляет новые). Если секреты не заданы — блок S3 не меняется.

**Важно:** `.env` на сервере должен быть создан до первого деплоя (из `.env.example`) с базовыми переменными (DATABASE_URL, OAUTH_*, OPENAI_API_KEY и т.д.). Deploy только обновляет S3-переменные, остальное не трогает.

### Переменные окружения для сервера (.env)

**Не хранить полный `.env` в GitHub Secrets!**

Вариант 1 (рекомендуется):
- Создать `.env` на сервере вручную один раз из `.env.example`
- Не перезаписывать из CI

Вариант 2:
- Каждую чувствительную переменную добавить отдельным секретом (например `SECRET_POSTGRES_PASSWORD`, `SECRET_OAUTH_SECRET_KEY`)
- В шаге деплоя генерировать `.env` из секретов

**Список переменных для production (из `.env.example`):**

```bash
# Database
POSTGRES_USER=contentfactory
POSTGRES_PASSWORD=<сгенерировать>
POSTGRES_DB=contentfactory
DATABASE_URL=postgresql+asyncpg://contentfactory:<пароль>@postgres:5432/contentfactory

# Security
OAUTH_SECRET_KEY=<сгенерировать>
OAUTH_ENCRYPTION_SALT=<сгенерировать>

# AI Providers
OPENAI_API_KEY=<ваш ключ>
OPENAI_MODEL=gpt-4o-mini

# Replicate
REPLICATE_API_TOKEN=<ваш токен>
IMAGE_PROVIDER=replicate
REPLICATE_IMAGE_MODEL=<модель для image-to-image>
REPLICATE_VIDEO_MODEL=<модель для image-to-video>
REPLICATE_DELAY_SECONDS=15

# Хранение медиа (Этап 10)
# local = локальная FS, s3 = S3 (production)
STORAGE_BACKEND=local
MEDIA_BASE_PATH=./media
# Для S3 (при STORAGE_BACKEND=s3):
# S3_ACCESS_KEY_ID=
# S3_SECRET_ACCESS_KEY=
# S3_BUCKET=
# S3_REGION=us-east-1
# S3_ENDPOINT_URL=
# S3_PUBLIC_URL=
# S3_PRESIGNED_EXPIRE=3600

# VK video upload (опционально)
VK_SERVICE_KEY=<сервисный ключ VK>
VK_GROUP_ID=<ID сообщества>
VK_COMMUNITY_TOKEN=<токен сообщества>

# Frontend
VITE_API_BASE_URL=/api
```

**Важно:** Все пароли и ключи генерировать уникальными для production. Не использовать дефолтные значения из docker-compose.yml.

---

## Настройка сервера

### Требования

- **ОС:** Ubuntu 20.04+ или Debian 11+
- **Docker:** 24.0+
- **Docker Compose:** 2.20+
- **Git:** установлен
- **SSH:** доступ по ключу

### Подготовка сервера

#### 1. Установка Docker и Docker Compose

```bash
# Обновление пакетов
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo apt install docker-compose-plugin -y

# Проверка
docker --version
docker compose version
```

#### 2. Создание пользователя для деплоя

```bash
# Создание пользователя deploy
sudo adduser deploy

# Добавление в группу docker
sudo usermod -aG docker deploy

# Переключение на пользователя deploy
sudo su - deploy
```

#### 3. Настройка SSH-ключа

**На локальной машине:**

```bash
# Генерация SSH-ключа (если нет)
ssh-keygen -t ed25519 -C "deploy@contentfactory" -f ~/.ssh/contentfactory_deploy

# Копирование публичного ключа на сервер
ssh-copy-id -i ~/.ssh/contentfactory_deploy.pub deploy@<server_ip>
```

**Добавление приватного ключа в GitHub Secrets:**

```bash
# Вывести содержимое приватного ключа
cat ~/.ssh/contentfactory_deploy

# Скопировать весь вывод (включая BEGIN и END строки)
# Добавить в GitHub Secrets как SSH_PRIVATE_KEY
```

#### 4. Настройка директории деплоя

**На сервере (под пользователем deploy):**

```bash
# Создание директории
sudo mkdir -p /var/www/contentfactory
sudo chown deploy:deploy /var/www/contentfactory

# Переход в директорию
cd /var/www/contentfactory

# Клонирование репозитория
git clone https://github.com/<your-org>/ContentFactory.git .

# Настройка git для pull без интерактивного ввода
git config pull.rebase false
```

---

## Структура файлов на сервере

### Рекомендуемая структура

```
/var/www/contentfactory/          # DEPLOY_PATH
├── .env                          # Переменные окружения (создать вручную)
├── .git/                         # Git репозиторий
├── docker-compose.yml            # Из репозитория
├── docker-compose.prod.yml       # Опционально: переопределения для prod
├── nginx-ssl.conf                # Конфиг nginx для SSL (из репо)
├── certs/                        # Сертификаты SSL (не в git)
│   ├── fullchain.pem
│   └── privkey.pem
├── backend/                      # Код backend
├── frontend/                     # Код frontend
├── scripts/                      # Скрипты
└── media/                        # Volume для медиа (при STORAGE_BACKEND=local)
```

**При использовании S3:** при `STORAGE_BACKEND=s3` директория `media/` не используется — все медиа хранятся в S3. Volume можно не монтировать или оставить пустым.

### Что откуда брать

| Файл / каталог | Откуда | Куда на сервере |
|----------------|--------|------------------|
| `docker-compose.yml` | Репозиторий (корень) | `$DEPLOY_PATH/docker-compose.yml` |
| `docker-compose.prod.yml` | Репозиторий или свой | `$DEPLOY_PATH/docker-compose.prod.yml` |
| `.env` | **Не из git!** Создать вручную из `.env.example` | `$DEPLOY_PATH/.env` |
| `nginx-ssl.conf` | Репозиторий (корень) | `$DEPLOY_PATH/nginx-ssl.conf` |
| `certs/` | Получить через certbot или загрузить свои | `$DEPLOY_PATH/certs/` |
| Код backend/frontend | `git pull` в `$DEPLOY_PATH` | `$DEPLOY_PATH/backend`, `$DEPLOY_PATH/frontend` |
| Образы Docker | GitHub Actions → ghcr.io; на сервере `docker compose pull` | Не сохранять вручную |

---

## Первое развёртывание

### Шаг 1: Создание .env на сервере

```bash
cd /var/www/contentfactory

# Копирование примера
cp .env.example .env

# Редактирование (использовать nano, vim или другой редактор)
nano .env
```

**Заполнить все секреты:**
- `POSTGRES_PASSWORD` — сгенерировать сильный пароль
- `OAUTH_SECRET_KEY` — сгенерировать (например: `openssl rand -hex 32`)
- `OAUTH_ENCRYPTION_SALT` — сгенерировать (например: `openssl rand -hex 16`)
- `OPENAI_API_KEY` — ваш ключ OpenAI
- `REPLICATE_API_TOKEN` — ваш токен Replicate
- Другие переменные по необходимости

### Шаг 2: Получение SSL сертификатов (для production)

**Вариант 1: Let's Encrypt (Certbot)**

```bash
# Установка certbot
sudo apt install certbot -y

# Получение сертификата (standalone режим)
sudo certbot certonly --standalone -d yourdomain.com

# Копирование сертификатов в директорию проекта
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /var/www/contentfactory/certs/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /var/www/contentfactory/certs/
sudo chown deploy:deploy /var/www/contentfactory/certs/*
```

**Вариант 2: Самоподписанный сертификат (для dev/staging)**

```bash
mkdir -p /var/www/contentfactory/certs
cd /var/www/contentfactory/certs

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout privkey.pem -out fullchain.pem \
  -subj "/CN=yourdomain.com"
```

### Шаг 3: Запуск приложения

```bash
cd /var/www/contentfactory

# Запуск сервисов
docker compose up -d

# Проверка статуса
docker compose ps

# Просмотр логов
docker compose logs -f

# Выполнение миграций
docker compose exec backend alembic upgrade head
```

### Шаг 4: Проверка работоспособности

```bash
# Health check
curl http://localhost:8000/health

# Проверка frontend (если настроен nginx)
curl http://localhost:80

# Проверка логов
docker compose logs backend --tail=50
docker compose logs frontend --tail=50
```

### Шаг 5: Настройка GitHub Secrets

В GitHub Repository → Settings → Secrets and variables → Actions добавить:

```
SSH_HOST = <IP или домен сервера>
SSH_USER = deploy
SSH_PRIVATE_KEY = <содержимое ~/.ssh/contentfactory_deploy>
SSH_PORT = 22
DEPLOY_PATH = /var/www/contentfactory
```

### Шаг 6: Тестовый деплой

**Вариант 1: Ручной запуск**

1. Перейти в GitHub → Actions
2. Выбрать workflow "Deploy to Server"
3. Нажать "Run workflow"
4. Выбрать environment (production/staging)
5. Нажать "Run workflow"

**Вариант 2: Через git tag**

```bash
# На локальной машине
git tag v1.0.0
git push origin v1.0.0

# Workflow автоматически запустится
```

### Шаг 7: Мониторинг деплоя

1. Перейти в GitHub → Actions
2. Выбрать запущенный workflow
3. Следить за логами каждого job
4. При успехе — проверить приложение на сервере

---

## Локальные скрипты проверки

### scripts/check.sh

**Назначение:** Проверка кода перед коммитом (format, lint, tests).

**Использование:**

```bash
# Из корня проекта
./scripts/check.sh
```

**Что проверяет:**

1. **Backend:**
   - Black (format check)
   - Ruff (lint)
   - Pyright (type check, опционально)
   - Pytest (tests)

2. **Frontend:**
   - ESLint
   - TypeScript (tsc --noEmit)
   - Build check

**Результат:**
- При успехе — выводит сообщение "Все проверки пройдены успешно"
- При ошибке — останавливается и выводит ошибку

### scripts/commit_checked.sh

**Назначение:** Проверка кода и создание коммита в одном шаге.

**Использование:**

```bash
# Из корня проекта
./scripts/commit_checked.sh "сообщение коммита"

# Примеры
./scripts/commit_checked.sh "добавлена функция импорта товаров"
./scripts/commit_checked.sh "исправлена ошибка в валидации"
```

**Что делает:**

1. Запускает `./scripts/check.sh`
2. При успехе — выполняет `git add .`
3. Показывает список изменений
4. Запрашивает подтверждение
5. Создаёт коммит с указанным сообщением
6. Выводит информацию о коммите

**Результат:**
- При ошибках проверки — коммит не создаётся
- При успехе — коммит создан, готов к push

### Настройка прав выполнения

**На Linux/Mac:**

```bash
chmod +x scripts/check.sh
chmod +x scripts/commit_checked.sh
```

**На Windows (Git Bash):**

```bash
git update-index --chmod=+x scripts/check.sh
git update-index --chmod=+x scripts/commit_checked.sh
```

---

## Troubleshooting

### CI падает на тестах

**Проблема:** Job `backend-test` падает.

**Решения:**

1. Проверить логи тестов в GitHub Actions
2. Запустить тесты локально:
   ```bash
   cd backend
   pytest tests/ -v
   ```
3. Проверить переменные окружения в CI (DATABASE_URL, API ключи)
4. Убедиться, что PostgreSQL сервис запустился (health check)

### Миграции не применяются

**Проблема:** Job `backend-migrations` падает.

**Решения:**

1. Проверить синтаксис миграций
2. Запустить миграции локально:
   ```bash
   cd backend
   alembic upgrade head
   ```
3. Проверить `alembic.ini` и `env.py`
4. Убедиться, что `DATABASE_URL` корректен

### Build падает на Docker

**Проблема:** Job `build-backend` или `build-frontend` падает.

**Решения:**

1. Проверить Dockerfile на ошибки
2. Собрать образ локально:
   ```bash
   docker build -t test-backend ./backend
   docker build -t test-frontend ./frontend
   ```
3. Проверить права на push в ghcr.io (GITHUB_TOKEN)
4. Убедиться, что репозиторий публичный или настроены права на packages

### Деплой не подключается к серверу

**Проблема:** Job `deploy` падает на SSH.

**Решения:**

1. Проверить SSH_HOST, SSH_USER, SSH_PORT в Secrets
2. Проверить SSH_PRIVATE_KEY (должен быть полный ключ с BEGIN/END)
3. Проверить доступность сервера:
   ```bash
   ssh -i ~/.ssh/deploy_key deploy@<server_ip>
   ```
4. Проверить `known_hosts` (может потребоваться добавить хост вручную)

### Деплой падает на git pull

**Проблема:** На сервере не удаётся выполнить `git pull`.

**Решения:**

1. На сервере проверить статус git:
   ```bash
   cd /var/www/contentfactory
   git status
   ```
2. Если есть локальные изменения — сбросить:
   ```bash
   git reset --hard HEAD
   git pull origin main
   ```
3. Проверить права на директорию:
   ```bash
   ls -la /var/www/contentfactory
   ```

### Docker compose не запускается

**Проблема:** `docker compose up -d` падает на сервере.

**Решения:**

1. Проверить логи:
   ```bash
   docker compose logs
   ```
2. Проверить `.env` (все переменные заполнены?)
3. Проверить порты (не заняты ли 8000, 5432, 80?)
4. Проверить версию Docker Compose:
   ```bash
   docker compose version
   ```
5. Попробовать запустить вручную:
   ```bash
   docker compose up
   ```

### Миграции не применяются на сервере

**Проблема:** `alembic upgrade head` падает в деплое.

**Решения:**

1. Проверить, что backend контейнер запущен:
   ```bash
   docker compose ps
   ```
2. Выполнить миграции вручную:
   ```bash
   docker compose exec backend alembic upgrade head
   ```
3. Проверить логи backend:
   ```bash
   docker compose logs backend
   ```
4. Проверить DATABASE_URL в .env на сервере

### Backend и frontend не запускаются после перезагрузки сервера

**Проблема:** После перезагрузки сервера контейнеры backend и frontend не запущены (502).

**Решения:**

1. **Проверить crontab на сервере:**
   ```bash
   crontab -l
   ```
   Должна быть строка:
   ```
   @reboot sleep 45 && cd /opt/contentfactory && GHCR_OWNER=astalex-s docker compose -f docker-compose.prod.yml --env-file .env up -d
   ```
   (путь и GHCR_OWNER зависят от вашей настройки)

2. **При необходимости установить systemd вручную** (если deploy-пользователь не имеет прав):
   ```bash
   sudo cp deploy/contentfactory.service /etc/systemd/system/
   sudo sed -i "s|__DEPLOY_PATH__|/opt/contentfactory|g" /etc/systemd/system/contentfactory.service
   sudo systemctl daemon-reload && sudo systemctl enable contentfactory
   ```

3. **Проверить restart в docker-compose.prod.yml:**
   - Должно быть `restart: always` для postgres, backend, frontend

4. **Запустить контейнеры вручную:**
   ```bash
   cd /opt/contentfactory
   GHCR_OWNER=astalex-s docker compose -f docker-compose.prod.yml --env-file .env up -d
   ```

### Образы не скачиваются с ghcr.io

**Проблема:** `docker compose pull` не может скачать образы.

**Решения:**

1. Проверить, что образы опубликованы:
   - Перейти в GitHub → Packages
   - Найти `contentfactory-backend` и `contentfactory-frontend`
2. Если репозиторий приватный — настроить аутентификацию:
   ```bash
   docker login ghcr.io -u <username> -p <token>
   ```
3. Проверить теги образов в docker-compose.yml
4. Попробовать pull вручную:
   ```bash
   docker pull ghcr.io/<owner>/contentfactory-backend:latest
   ```

---

## Дополнительные рекомендации

### Мониторинг и логирование

**На сервере:**

```bash
# Просмотр логов в реальном времени
docker compose logs -f

# Логи конкретного сервиса
docker compose logs -f backend

# Последние N строк
docker compose logs --tail=100 backend
```

**Настройка log rotation (опционально):**

Создать `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Перезапустить Docker:

```bash
sudo systemctl restart docker
```

### Backup базы данных

**Создание backup:**

```bash
docker compose exec postgres pg_dump -U contentfactory contentfactory > backup_$(date +%Y%m%d_%H%M%S).sql
```

**Восстановление:**

```bash
docker compose exec -T postgres psql -U contentfactory contentfactory < backup_20260227_120000.sql
```

### Автоматическое обновление SSL сертификатов

**Настройка cron для certbot:**

```bash
sudo crontab -e

# Добавить строку (обновление каждый день в 3:00)
0 3 * * * certbot renew --quiet && cp /etc/letsencrypt/live/yourdomain.com/*.pem /var/www/contentfactory/certs/ && docker compose -f /var/www/contentfactory/docker-compose.yml restart nginx
```

### Мониторинг здоровья приложения

**Использование health checks:**

В `docker-compose.yml` добавить:

```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**Проверка статуса:**

```bash
docker compose ps
```

---

## Контакты и поддержка

При возникновении проблем:

1. Проверить логи в GitHub Actions
2. Проверить логи на сервере (`docker compose logs`)
3. Обратиться к документации:
   - [GitHub Actions](https://docs.github.com/en/actions)
   - [Docker Compose](https://docs.docker.com/compose/)
   - [Alembic](https://alembic.sqlalchemy.org/)

---

**Документация актуальна на:** февраль 2026
