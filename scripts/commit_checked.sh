#!/bin/bash

# Скрипт для проверки кода и создания коммита
# Использование: ./scripts/commit_checked.sh "сообщение коммита"

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка аргументов
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Ошибка: не указано сообщение коммита${NC}"
    echo ""
    echo "Использование:"
    echo "  ./scripts/commit_checked.sh \"сообщение коммита\""
    echo ""
    echo "Примеры:"
    echo "  ./scripts/commit_checked.sh \"добавлена функция импорта товаров\""
    echo "  ./scripts/commit_checked.sh \"исправлена ошибка в валидации\""
    exit 1
fi

COMMIT_MESSAGE="$1"

echo "======================================"
echo "🚀 Проверка и коммит"
echo "======================================"
echo ""
echo "Сообщение коммита: $COMMIT_MESSAGE"
echo ""

# Запуск проверок
echo "======================================"
echo "🔍 Запуск проверок кода..."
echo "======================================"

if ! ./scripts/check.sh; then
    echo ""
    echo -e "${RED}❌ Проверки не прошли. Коммит отменён.${NC}"
    echo ""
    echo "Исправьте ошибки и попробуйте снова."
    exit 1
fi

echo ""
echo "======================================"
echo "📝 Создание коммита..."
echo "======================================"

# Добавление всех изменений
git add .

# Проверка наличия изменений
if git diff --cached --quiet; then
    echo -e "${YELLOW}⚠️  Нет изменений для коммита${NC}"
    exit 0
fi

# Показать что будет закоммичено
echo ""
echo "Файлы для коммита:"
git diff --cached --name-status

echo ""
read -p "Продолжить коммит? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠️  Коммит отменён пользователем${NC}"
    exit 0
fi

# Создание коммита
git commit -m "$COMMIT_MESSAGE"

echo ""
echo "======================================"
echo -e "${GREEN}✅ Коммит успешно создан!${NC}"
echo "======================================"
echo ""
echo "Последний коммит:"
git log -1 --oneline
echo ""
echo "Для отправки на сервер выполните:"
echo "  git push origin $(git branch --show-current)"
echo ""
