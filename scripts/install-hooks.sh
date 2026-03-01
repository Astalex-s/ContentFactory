#!/bin/bash
# Устанавливает git hooks для проверки кода перед push.
# Запустите из корня проекта: ./scripts/install-hooks.sh

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOKS="$ROOT/.git/hooks"
PREPUSH="$ROOT/scripts/pre-push.sh"

if [ ! -d "$ROOT/.git" ]; then
    echo "Ошибка: .git не найден. Запустите из корня репозитория."
    exit 1
fi

mkdir -p "$HOOKS"
cat > "$HOOKS/pre-push" << EOF
#!/bin/bash
exec "$PREPUSH"
EOF
chmod +x "$HOOKS/pre-push"
chmod +x "$PREPUSH" 2>/dev/null || true

echo "✅ Pre-push hook установлен: $HOOKS/pre-push"
echo "   Перед каждым push будет запускаться scripts/check.sh"
