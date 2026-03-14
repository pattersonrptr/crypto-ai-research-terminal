#!/usr/bin/env bash
# Run CI checks locally — mirrors .github/workflows/ci.yml exactly.
# Must pass before opening a PR.
#
# Usage:
#   ./scripts/ci-local.sh          # run all checks
#   ./scripts/ci-local.sh --fix    # run ruff with --fix before checking
#
# Exit code: 0 = all green, non-zero = at least one check failed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FIX_MODE=0

for arg in "$@"; do
    [[ "$arg" == "--fix" ]] && FIX_MODE=1
done

cd "$PROJECT_ROOT"

# Activate virtual environment if not already active
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    source .venv/bin/activate
fi

echo "🔍 Running CI checks locally (mirrors GitHub Actions)..."
echo ""

# ---------------------------------------------------------------------------
# job: quality
# ---------------------------------------------------------------------------

echo "=== [quality] 1/4 RUFF (lint) ==="
if [[ $FIX_MODE -eq 1 ]]; then
    ruff check backend/ --fix
else
    ruff check backend/
fi
echo "✅ Ruff lint passed"
echo ""

echo "=== [quality] 2/4 RUFF FORMAT ==="
if [[ $FIX_MODE -eq 1 ]]; then
    ruff format backend/
else
    ruff format --check backend/
fi
echo "✅ Ruff format passed"
echo ""

echo "=== [quality] 3/4 MYPY (type check) ==="
# Mirrors CI: checks backend/app only (scripts/ excluded from strict mypy)
mypy backend/app --config-file=pyproject.toml
echo "✅ Mypy passed"
echo ""

echo "=== [quality] 4/4 BANDIT (security) ==="
bandit -c pyproject.toml -r backend/app -q
echo "✅ Bandit passed"
echo ""

# ---------------------------------------------------------------------------
# job: test (needs: quality)
# ---------------------------------------------------------------------------

echo "=== [test] PYTEST (full suite + coverage) ==="
pytest backend/tests/ --tb=short -q
echo ""

echo "🎉 All CI checks passed! Safe to open a PR."
