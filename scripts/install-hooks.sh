#!/bin/bash
# Устанавливает git hooks: pre-commit (black) и pre-push (check).
# Запустите из корня проекта: ./scripts/install-hooks.sh

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOKS="$ROOT/.git/hooks"
PRECOMMIT="$ROOT/scripts/pre-commit.sh"
PREPUSH="$ROOT/scripts/pre-push.sh"

if [ ! -d "$ROOT/.git" ]; then
    echo "Ошибка: .git не найден. Запустите из корня репозитория."
    exit 1
fi

mkdir -p "$HOOKS"

# Pre-commit: black форматирует код — CI не падает на format check
cat > "$HOOKS/pre-commit" << EOF
#!/bin/bash
exec "$PRECOMMIT"
EOF
chmod +x "$HOOKS/pre-commit"
chmod +x "$PRECOMMIT" 2>/dev/null || true

# Pre-push: полная проверка (black --check, ruff, pyright, tests)
cat > "$HOOKS/pre-push" << EOF
#!/bin/bash
exec "$PREPUSH"
EOF
chmod +x "$HOOKS/pre-push"
chmod +x "$PREPUSH" 2>/dev/null || true

echo "✅ Pre-commit hook: black форматирует код перед коммитом"
echo "✅ Pre-push hook: scripts/check.sh перед push"
echo "   Установка: $HOOKS/pre-commit, $HOOKS/pre-push"
