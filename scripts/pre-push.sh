#!/bin/bash
# Pre-push hook: запускает проверки перед push.
# Установка: ./scripts/install-hooks.sh

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "🔍 Pre-push: проверка кода..."
if [ -x "./scripts/check.sh" ]; then
    ./scripts/check.sh
else
    echo "Запуск black, ruff, pyright..."
    cd backend
    python -m black --check app/ tests/ || { echo "Black failed. Run: black app/ tests/"; exit 1; }
    python -m ruff check app/ tests/ || { echo "Ruff failed."; exit 1; }
    python -m pyright app/ || { echo "Pyright failed."; exit 1; }
    cd ..
fi
echo "✅ Pre-push проверки пройдены"
