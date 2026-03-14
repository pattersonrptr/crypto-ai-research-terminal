#!/usr/bin/env bash
# Run CI checks locally before pushing
# Usage: ./scripts/ci-local.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Activate virtual environment if not already active
if [[ -z "$VIRTUAL_ENV" ]]; then
    source .venv/bin/activate
fi

echo "🔍 Running CI checks locally..."
echo ""

echo "=== 1/5 RUFF (lint) ==="
ruff check backend/
echo "✅ Ruff lint passed"
echo ""

echo "=== 2/5 RUFF FORMAT ==="
ruff format --check backend/
echo "✅ Ruff format passed"
echo ""

echo "=== 3/5 MYPY (type check) ==="
mypy backend/app
echo "✅ Mypy passed"
echo ""

echo "=== 4/5 BANDIT (security) ==="
bandit -c pyproject.toml -r backend/app -q
echo "✅ Bandit passed"
echo ""

echo "=== 5/5 PYTEST ==="
pytest backend/tests/ --tb=short -q
echo ""

echo "🎉 All CI checks passed! Safe to push."
