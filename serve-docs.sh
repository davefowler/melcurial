#!/usr/bin/env bash
set -euo pipefail

# Serve the docs/ directory locally
# Usage: scripts/serve-docs.sh [port]

PORT="${1:-8000}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Serving docs from $ROOT_DIR/docs at http://localhost:${PORT}/"

if command -v python3 >/dev/null 2>&1; then
  exec python3 -m http.server --directory docs "${PORT}"
else
  echo "python3 not found. Please install Python 3 to use this script." >&2
  exit 1
fi


