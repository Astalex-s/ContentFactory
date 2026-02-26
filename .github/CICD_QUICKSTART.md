# CI/CD Quick Start Guide

Быстрая инструкция по настройке CI/CD для ContentFactory.

## 📋 Что уже настроено

✅ **Workflows:**
- `.github/workflows/ci.yml` — автоматическая проверка кода
- `.github/workflows/build.yml` — сборка Docker-образов
- `.github/workflows/deploy.yml` — деплой на сервер

✅ **Локальные скрипты:**
- `scripts/check.sh` — проверка кода перед коммитом
- `scripts/commit_checked.sh` — проверка + коммит

✅ **Конфигурация:**
- `backend/pyproject.toml` — настройки black, ruff, pyright, pytest

---

## 🚀 Быстрая настройка

### 1. Настройка GitHub Secrets (для деплоя)

Перейдите в **GitHub Repository → Settings → Secrets and variables → Actions** и добавьте:

```
SSH_HOST = <IP или домен сервера>
SSH_USER = deploy
SSH_PRIVATE_KEY = <содержимое приватного SSH-ключа>
SSH_PORT = 22
DEPLOY_PATH = /var/www/contentfactory
```

### 2. Подготовка сервера

```bash
# На сервере
sudo adduser deploy
sudo usermod -aG docker deploy
sudo mkdir -p /var/www/contentfactory
sudo chown deploy:deploy /var/www/contentfactory

# Клонирование репозитория
su - deploy
cd /var/www/contentfactory
git clone <repository-url> .

# Создание .env
cp .env.example .env
nano .env  # Заполнить все секреты

# Первый запуск
docker compose up -d
docker compose exec backend alembic upgrade head
```

### 3. Локальная разработка

```bash
# Проверка кода перед коммитом
./scripts/check.sh

# Проверка + коммит
./scripts/commit_checked.sh "добавлена функция импорта"

# Права выполнения (Linux/Mac)
chmod +x scripts/*.sh

# Windows (Git Bash)
git update-index --chmod=+x scripts/check.sh
git update-index --chmod=+x scripts/commit_checked.sh
```

---

## 🔄 Как работает CI/CD

### Автоматический workflow

```
git push → CI → Build → Deploy
```

1. **Push в main/develop** → запускается CI
2. **CI проходит успешно** → запускается Build
3. **Build завершён** → запускается Deploy (только для main)

### Ручной деплой

1. Перейти в **GitHub → Actions**
2. Выбрать workflow "Deploy to Server"
3. Нажать "Run workflow"
4. Выбрать environment (production/staging)

### Деплой по тегу

```bash
git tag v1.0.0
git push origin v1.0.0
```

Автоматически запустится Build → Deploy.

---

## ✅ Что проверяет CI

### Backend
- ✅ Black (format check)
- ✅ Ruff (lint)
- ✅ Pyright (type check)
- ✅ Pytest (unit + integration tests)
- ✅ Alembic migrations

### Frontend
- ✅ ESLint
- ✅ TypeScript (tsc --noEmit)
- ✅ Build check

---

## 🛠️ Troubleshooting

### CI падает на тестах

```bash
# Запустить тесты локально
cd backend
pytest tests/ -v
```

### Миграции не применяются

```bash
# Проверить миграции локально
cd backend
alembic upgrade head
alembic current
```

### Деплой не подключается к серверу

```bash
# Проверить SSH подключение
ssh -i ~/.ssh/deploy_key deploy@<server_ip>

# Проверить права на директорию
ls -la /var/www/contentfactory
```

### Docker compose не запускается

```bash
# На сервере
cd /var/www/contentfactory
docker compose logs
docker compose ps
```

---

## 📚 Полная документация

Подробная документация: **`docs/CI_CD.md`**

Включает:
- Детальное описание всех workflows
- Полный список GitHub Secrets
- Пошаговая инструкция настройки сервера
- Структура файлов на сервере
- Мониторинг и логирование
- Backup базы данных
- SSL сертификаты

---

## 🔐 Важные напоминания

1. ❌ **Никогда не коммитьте** `.env` файлы
2. ❌ **Никогда не коммитьте** приватные SSH-ключи
3. ✅ **Всегда используйте** GitHub Secrets для чувствительных данных
4. ✅ **Всегда запускайте** `./scripts/check.sh` перед push
5. ✅ **Всегда проверяйте** статус CI перед merge

---

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в GitHub Actions
2. Проверьте логи на сервере (`docker compose logs`)
3. Обратитесь к `docs/CI_CD.md`
