#!/usr/bin/env bash
# Lanza backend (FastAPI :8000) y frontend (Vite :5173) en modo dev con hot reload.
#
#   ./dev.sh         → backend + frontend
#   ./dev.sh back    → solo backend
#   ./dev.sh front   → solo frontend
#
# Los datos de dev se guardan en ./data (ignorado por git). La app se usa
# desde http://localhost:5173 (Vite proxya /api al backend).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="${TT_DATA_DIR:-$ROOT/data}"
MODE="${1:-all}"

start_back() {
  if ! command -v uv >/dev/null 2>&1; then
    echo "✗ uv no encontrado. Instálalo con:" >&2
    echo "    sudo pacman -S uv        # Arch/CachyOS" >&2
    echo "    curl -LsSf https://astral.sh/uv/install.sh | sh   # cualquier distro" >&2
    exit 1
  fi
  cd "$ROOT/backend"
  mkdir -p "$DATA_DIR"
  uv sync
  TT_DATA_DIR="$DATA_DIR" uv run alembic upgrade head
  echo "▸ Backend: http://localhost:8000 (API docs: http://localhost:8000/api/docs)"
  TT_DATA_DIR="$DATA_DIR" exec uv run uvicorn app.asgi:app --reload --port 8000
}

start_front() {
  if ! command -v npm >/dev/null 2>&1; then
    echo "✗ npm no encontrado. Instala Node 22+ (https://nodejs.org) para el modo dev del frontend." >&2
    exit 1
  fi
  cd "$ROOT/frontend"
  if [ ! -d node_modules ]; then
    echo "▸ Instalando dependencias del frontend…"
    npm install --no-audit --no-fund
  fi
  echo "▸ Frontend: http://localhost:5173 (proxy /api → :8000)"
  exec npm run dev
}

case "$MODE" in
  back) start_back ;;
  front) start_front ;;
  all)
    start_back &
    BACK_PID=$!
    trap 'kill "$BACK_PID" 2>/dev/null || true' EXIT INT TERM
    start_front
    ;;
  *)
    echo "Uso: ./dev.sh [back|front]" >&2
    exit 1
    ;;
esac
