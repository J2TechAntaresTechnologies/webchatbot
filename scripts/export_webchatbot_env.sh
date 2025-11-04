#!/usr/bin/env bash
# Configura las variables de entorno necesarias para el proyecto webchatbot.

if [[ "${BASH_SOURCE[0]:-}" == "${0}" ]]; then
    set -euo pipefail
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

export WEBCHATBOT_PROJECT_ROOT="${PROJECT_ROOT}"

# Asegura que el proyecto esté en PYTHONPATH solo una vez.-----------
case ":${PYTHONPATH:-}:" in
    *:"${PROJECT_ROOT}":*) ;;  # ya está presente
    ::)
        export PYTHONPATH="${PROJECT_ROOT}"
        ;;
    *)
        export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"
        ;;
esac

# Permite definir un modelo por defecto sin sobreescribir LLM_MODEL_PATH explícito.
# Preferencia: primer .gguf en ${PROJECT_ROOT}/modelos si existe; si no, ruta por defecto del sistema.
MODELS_DIR="${PROJECT_ROOT}/modelos"
if [[ -z "${WEBCHATBOT_DEFAULT_LLM_MODEL_PATH:-}" ]]; then
    if compgen -G "${MODELS_DIR}"/*.gguf > /dev/null 2>&1; then
        FIRST_GGUF=$(ls -1 "${MODELS_DIR}"/*.gguf 2>/dev/null | head -n 1 || true)
        WEBCHATBOT_DEFAULT_LLM_MODEL_PATH="${FIRST_GGUF:-}"
    fi
fi

: "${WEBCHATBOT_DEFAULT_LLM_MODEL_PATH:=/home/jim/.cache/llama.cpp/ggml-org_gemma-3-1b-it-GGUF_gemma-3-1b-it-Q4_K_M.gguf}"
export WEBCHATBOT_DEFAULT_LLM_MODEL_PATH
DEFAULT_LLM_PATH="${WEBCHATBOT_DEFAULT_LLM_MODEL_PATH}"
if [[ -z "${LLM_MODEL_PATH:-}" && -n "${DEFAULT_LLM_PATH}" ]]; then
    export LLM_MODEL_PATH="${DEFAULT_LLM_PATH}"
fi

if [[ -n "${LLM_MODEL_PATH:-}" && ! -f "${LLM_MODEL_PATH}" ]]; then
    echo "[WARN] LLM_MODEL_PATH apunta a un archivo inexistente: ${LLM_MODEL_PATH}" >&2
    echo "       Ajustá WEBCHATBOT_DEFAULT_LLM_MODEL_PATH o exportá LLM_MODEL_PATH antes de activar el venv." >&2
fi

# Directorio base de datos/conocimiento para usos futuros.
export WEBCHATBOT_DATA_DIR="${WEBCHATBOT_DATA_DIR:-${PROJECT_ROOT}/knowledge}"

# Mostrar un resumen del contexto al activar (puede deshabilitarse con WEBCHATBOT_CONTEXT_ON_ACTIVATE=0)
if [[ "${WEBCHATBOT_CONTEXT_ON_ACTIVATE:-1}" != "0" ]]; then
    CTX_FILE="${PROJECT_ROOT}/contexto.txt"
    if [[ -f "${PROJECT_ROOT}/bin/python" && -f "${PROJECT_ROOT}/scripts/context_manager.py" ]]; then
        "${PROJECT_ROOT}/bin/python" "${PROJECT_ROOT}/scripts/context_manager.py" show --brief || true
    elif [[ -f "${CTX_FILE}" ]]; then
        echo "=== Último contexto (tail) ==="
        tail -n 40 "${CTX_FILE}" || true
        echo "=== Fin contexto ==="
    fi
fi
