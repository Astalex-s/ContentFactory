#!/bin/bash
# Pre-commit hook: автоматически форматирует код перед коммитом.
# Black форматирует Python — код в коммите всегда соответствует CI.
# Установка: ./scripts/install-hooks.sh

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -d "backend" ]; then
    exit 0
fi

echo "🔧 Pre-commit: black форматирует backend..."
cd backend
python -m black app/ tests/ 2>/dev/null || true
cd ..

# Добавить отформатированные файлы в индекс (только изменённые tracked)
git add -u backend/ 2>/dev/null || true

exit 0
