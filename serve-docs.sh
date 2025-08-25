#!/usr/bin/env bash
set -euo pipefail

# Serve the docs/ directory locally
# Usage: scripts/serve-docs.sh [port]

PORT="${1:-8331}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "Building docs with Jinja2…"
if command -v python3 >/dev/null 2>&1; then
  if python3 -c "import jinja2" >/dev/null 2>&1; then
    python3 scripts/build_docs.py || true
  else
    echo "Setting up local venv for docs…"
    python3 -m venv .venv-docs
    . ".venv-docs/bin/activate"
    python -m pip install --quiet Jinja2 || true
    python scripts/build_docs.py || true
    deactivate || true
  fi
else
  echo "python3 not found. Skipping docs build." >&2
fi

echo "Serving docs from $ROOT_DIR/docs at http://localhost:${PORT}/"

if command -v python3 >/dev/null 2>&1; then
  exec python3 -m http.server --directory docs "${PORT}"
else
  echo "python3 not found. Please install Python 3 to use this script." >&2
  exit 1
fi


