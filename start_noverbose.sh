#!/usr/bin/env bash
set -euo pipefail

# Variante silenciosa de start.sh
# - Reduce ruido de logs de llama.cpp via variables de entorno
# - Baja el nivel de logs de Uvicorn

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

# Ajustes de verbosidad para llama.cpp y Uvicorn (solo entorno)
# Notas:
# - GGML_LOG_LEVEL=ERROR silencia la mayoría de logs del backend ggml/llama.cpp
# - LLAMA_LOG_LEVEL=ERROR se incluye por compatibilidad en algunas builds
# - LLAMA_LOG_COLORS=0 evita códigos de color en logs
# - --log-level warning reduce el ruido de Uvicorn (sin afectar access logs)
LLM_ENV_PREFIX="GGML_LOG_LEVEL=ERROR LLAMA_LOG_LEVEL=ERROR LLAMA_LOG_COLORS=0"

API_CMD="${VENV_ACTIVATE}cd '$PROJECT_ROOT' && echo '[INFO] Iniciando API FastAPI en http://localhost:8000 (modo silencioso)' && env ${LLM_ENV_PREFIX} uvicorn services.api.main:app --reload --log-level warning"
FRONT_CMD="${VENV_ACTIVATE}cd '$PROJECT_ROOT' && echo '[INFO] Sirviendo frontend estático en http://localhost:5173' && python -m http.server --directory frontend 5173"

if command -v tmux >/dev/null 2>&1; then
  SESSION_NAME="chatbot_start_silent"
  if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "[ERROR] La sesión tmux '$SESSION_NAME' ya existe. Cerrala o elige otro nombre." >&2
    exit 1
  fi

  echo "[INFO] Creando sesión tmux '$SESSION_NAME'"
  tmux new-session -d -s "$SESSION_NAME" "$(command -v bash) -lc \"$API_CMD\""
  tmux split-window -v -t "$SESSION_NAME" "$(command -v bash) -lc \"$FRONT_CMD\""
  tmux select-layout -t "$SESSION_NAME" even-vertical
  tmux select-pane -t "$SESSION_NAME":0.0
  tmux display-message -t "$SESSION_NAME" "API → pane superior | Frontend → pane inferior (silencioso)"
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

# Recordatorio: la alternancia user/assistant depende del formato de mensajes
# que construya la aplicación. Este wrapper no modifica el código ni la carga
# de prompts; solo ajusta el nivel de logs por entorno.

