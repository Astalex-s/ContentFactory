#!/bin/bash

# Скрипт проверки кода перед коммитом
# Запускает format check, lint и тесты для backend и frontend

set -e

echo "======================================"
echo "🔍 Проверка кода перед коммитом"
echo "======================================"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода ошибок
error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Функция для вывода успеха
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Функция для вывода предупреждений
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Проверка наличия директорий
if [ ! -d "backend" ]; then
    error "Директория backend не найдена. Запустите скрипт из корня проекта."
fi

if [ ! -d "frontend" ]; then
    error "Директория frontend не найдена. Запустите скрипт из корня проекта."
fi

echo ""
echo "======================================"
echo "🐍 Backend: Format Check (Black)"
echo "======================================"
cd backend
if ! python -m black --check app/ tests/; then
    error "Black format check failed. Запустите: black app/ tests/"
fi
success "Black format check passed"

echo ""
echo "======================================"
echo "🐍 Backend: Lint (Ruff)"
echo "======================================"
if ! python -m ruff check app/ tests/; then
    error "Ruff lint failed. Запустите: ruff check --fix app/ tests/"
fi
success "Ruff lint passed"

echo ""
echo "======================================"
echo "🐍 Backend: Type Check (Pyright)"
echo "======================================"
if ! python -m pyright app/ 2>/dev/null; then
    error "Pyright type check failed. Установите: pip install pyright"
fi
success "Pyright type check passed"

echo ""
echo "======================================"
echo "🐍 Backend: Tests (Pytest)"
echo "======================================"
if ! python -m pytest tests/ -v --tb=short; then
    error "Pytest tests failed"
fi
success "Pytest tests passed"

cd ..

echo ""
echo "======================================"
echo "⚛️  Frontend: Lint (ESLint)"
echo "======================================"
cd frontend
if ! npm run lint; then
    error "ESLint failed"
fi
success "ESLint passed"

echo ""
echo "======================================"
echo "⚛️  Frontend: Type Check (TypeScript)"
echo "======================================"
if ! npx tsc --noEmit; then
    error "TypeScript check failed"
fi
success "TypeScript check passed"

echo ""
echo "======================================"
echo "⚛️  Frontend: Build Check"
echo "======================================"
if ! npm run build; then
    error "Frontend build failed"
fi
success "Frontend build passed"

cd ..

echo ""
echo "======================================"
echo -e "${GREEN}✅ Все проверки пройдены успешно!${NC}"
echo "======================================"
echo ""
echo "Теперь можно делать коммит:"
echo "  git add ."
echo "  git commit -m \"ваше сообщение\""
echo ""
echo "Или используйте скрипт commit_checked.sh:"
echo "  ./scripts/commit_checked.sh \"ваше сообщение\""
echo ""
