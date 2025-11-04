#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

VENV_ACTIVATE=""
if [ -f "$PROJECT_ROOT/bin/activate" ]; then
  VENV_ACTIVATE="source '$PROJECT_ROOT/bin/activate' && "
fi

# Mostrar último contexto (si existe)
if [ -x "$PROJECT_ROOT/bin/python" ] && [ -f "$PROJECT_ROOT/scripts/context_manager.py" ]; then
  bash -lc "${VENV_ACTIVATE}'$PROJECT_ROOT/bin/python' '$PROJECT_ROOT/scripts/context_manager.py' show --brief" || true
fi

if ! bash -lc "${VENV_ACTIVATE}command -v uvicorn" >/dev/null 2>&1; then
  cat <<'MSG'
[ERROR] No se encontró "uvicorn" en el PATH.
Instalá las dependencias con:
  make install-base
MSG
  exit 1
fi

if ! bash -lc "${VENV_ACTIVATE}command -v python" >/dev/null 2>&1; then
  echo "[ERROR] No se encontró python en el PATH." >&2
  exit 1
fi

API_CMD="${VENV_ACTIVATE}cd '$PROJECT_ROOT' && echo '[INFO] Iniciando API FastAPI en http://localhost:8000' && uvicorn services.api.main:app --reload"
FRONT_CMD="${VENV_ACTIVATE}cd '$PROJECT_ROOT' && echo '[INFO] Sirviendo frontend estático en http://localhost:5173' && python -m http.server --directory frontend 5173"

if command -v tmux >/dev/null 2>&1; then
  SESSION_NAME="chatbot_start"
  if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "[ERROR] La sesión tmux '$SESSION_NAME' ya existe. Cerrala o elige otro nombre." >&2
    exit 1
  fi

  echo "[INFO] Creando sesión tmux '$SESSION_NAME'"
  tmux new-session -d -s "$SESSION_NAME" "$(command -v bash) -lc \"$API_CMD\""
  tmux split-window -v -t "$SESSION_NAME" "$(command -v bash) -lc \"$FRONT_CMD\""
  tmux select-layout -t "$SESSION_NAME" even-vertical
  tmux select-pane -t "$SESSION_NAME":0.0
  tmux display-message -t "$SESSION_NAME" "API → pane superior | Frontend → pane inferior"
  tmux attach-session -t "$SESSION_NAME"
else
  echo "[WARN] tmux no está instalado. Se lanzarán procesos en segundo plano dentro de esta terminal."
  trap 'echo "\n[INFO] Deteniendo servicios..."; kill 0 2>/dev/null' EXIT
  bash -lc "$API_CMD" &
  API_PID=$!
  bash -lc "$FRONT_CMD" &
  FRONT_PID=$!
  echo "[INFO] Servicios en ejecución. Finalizá con Ctrl+C."
  wait -n "$API_PID" "$FRONT_PID"
fi
