#!/usr/bin/env bash
# Open a GitHub Pull Request — only after CI checks pass locally.
#
# Usage:
#   ./scripts/create-pr.sh --title "feat(x): ..." --body "..." [--base main]
#   ./scripts/create-pr.sh --title "feat(x): ..." --body-file pr-body.md
#   ./scripts/create-pr.sh --skip-ci --title "..."   # bypass local CI (discouraged)
#
# Requires: gh (GitHub CLI) — https://cli.github.com
#
# The script will:
#   1. Verify gh is installed and authenticated.
#   2. Run ./scripts/ci-local.sh (full quality + test suite).
#   3. Push the current branch to origin (if not already up to date).
#   4. Open the PR via `gh pr create`.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
SKIP_CI=0
PR_TITLE=""
PR_BODY=""
PR_BODY_FILE=""
PR_BASE="main"
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-ci)       SKIP_CI=1; shift ;;
        --title)         PR_TITLE="$2"; shift 2 ;;
        --body)          PR_BODY="$2"; shift 2 ;;
        --body-file)     PR_BODY_FILE="$2"; shift 2 ;;
        --base)          PR_BASE="$2"; shift 2 ;;
        *)               EXTRA_ARGS+=("$1"); shift ;;
    esac
done

# ---------------------------------------------------------------------------
# Validate required args
# ---------------------------------------------------------------------------
if [[ -z "$PR_TITLE" ]]; then
    echo "❌ --title is required."
    echo "Usage: $0 --title \"feat(scope): description\" [--body \"...\"] [--base main]"
    exit 1
fi

# ---------------------------------------------------------------------------
# Check gh is installed and authenticated
# ---------------------------------------------------------------------------
if ! command -v gh &>/dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    echo "   Install: https://cli.github.com"
    exit 1
fi

if ! gh auth status &>/dev/null; then
    echo "❌ GitHub CLI is not authenticated. Run: gh auth login"
    exit 1
fi

# ---------------------------------------------------------------------------
# Run CI locally (unless --skip-ci)
# ---------------------------------------------------------------------------
if [[ $SKIP_CI -eq 1 ]]; then
    echo "⚠️  --skip-ci passed — skipping local CI checks."
    echo "   This is strongly discouraged. CI will likely fail on GitHub."
    echo ""
else
    echo "🔍 Running CI checks before creating PR..."
    echo ""
    bash "$SCRIPT_DIR/ci-local.sh"
    echo ""
fi

# ---------------------------------------------------------------------------
# Push current branch
# ---------------------------------------------------------------------------
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "📤 Pushing branch '$BRANCH' to origin..."
git push --no-verify origin "$BRANCH"
echo ""

# ---------------------------------------------------------------------------
# Build gh pr create command
# ---------------------------------------------------------------------------
GH_ARGS=(
    --title "$PR_TITLE"
    --base "$PR_BASE"
    --head "$BRANCH"
)

if [[ -n "$PR_BODY_FILE" ]]; then
    GH_ARGS+=(--body-file "$PR_BODY_FILE")
elif [[ -n "$PR_BODY" ]]; then
    GH_ARGS+=(--body "$PR_BODY")
else
    # Open editor for body if neither --body nor --body-file was given
    GH_ARGS+=(--fill)
fi

if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
    GH_ARGS+=("${EXTRA_ARGS[@]}")
fi

# ---------------------------------------------------------------------------
# Create PR
# ---------------------------------------------------------------------------
echo "🚀 Creating PR: '$PR_TITLE' → $PR_BASE"
gh pr create "${GH_ARGS[@]}"
