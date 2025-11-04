"""Wrapper simple para el proveedor LLM."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Final

from services.llm_adapter.settings import LLMSettings

try:  # pragma: no cover - import opcional
    from llama_cpp import Llama  # type: ignore
except ImportError:  # pragma: no cover - import opcional
    Llama = None  # type: ignore

LOGGER = logging.getLogger(__name__)
PLACEHOLDER_REPLY: Final[str] = (
    "[LLM placeholder] Aún no estoy conectado a un modelo real. "
    "Se agregará generación dinámica en próximos sprints."
)


class LLMClient:
    """Cliente LLM que usa llama.cpp si hay un modelo local configurado."""

    def __init__(self, model_name: str = "llama-cpp", settings: LLMSettings | None = None) -> None:
        self.model_name = model_name
        self.settings = settings or LLMSettings()
        self._llama: Llama | None = None
        self._init_backend()

    def _init_backend(self) -> None:
        if not self.settings.has_model_path:
            LOGGER.info("LLM model path no configurado. Se usa respuesta placeholder.")
            return

        if Llama is None:
            LOGGER.warning(
                "llama-cpp-python no está instalado. Ejecutá 'pip install llama-cpp-python' "
                "o 'make install-rag' para usar un modelo local."
            )
            return

        model_path = self.settings.model_path
        if model_path is None or not model_path.exists():
            LOGGER.error("No se encontró el archivo GGUF en %s", model_path)
            return

        try:
            self._llama = Llama(
                model_path=str(model_path),
                n_ctx=self.settings.context_window,
                logits_all=False,
                embedding=False,
            )
            LOGGER.info("LLM local inicializado desde %s", model_path)
        except Exception:  # pragma: no cover - inicialización dependiente de entorno
            LOGGER.exception("Falló la inicialización del modelo LLaMA en %s", model_path)
            self._llama = None

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        if self._llama is None:
            return PLACEHOLDER_REPLY

        try:
            completion = await asyncio.to_thread(
                self._llama.create_completion,
                prompt=prompt,
                max_tokens=kwargs.get("max_tokens", self.settings.max_tokens),
                temperature=kwargs.get("temperature", self.settings.temperature),
                top_p=kwargs.get("top_p", self.settings.top_p),
                stream=False,
            )
        except Exception:  # pragma: no cover - depende del backend
            LOGGER.exception("Error generando respuesta con llama.cpp. Devuelvo placeholder.")
            return PLACEHOLDER_REPLY

        text = completion.get("choices", [{}])[0].get("text", "").strip()
        if not text:
            LOGGER.warning("Modelo LLaMA no generó texto. Devuelvo placeholder.")
            return PLACEHOLDER_REPLY
        return text

# ================================================================
# Guía de uso y parametrización (Cliente LLM)
# ================================================================
#
# ¿Qué hace?
# -----------
# Envuelve un backend LLM (llama.cpp opcional). Si no hay modelo/config,
# devuelve un placeholder seguro. Registra eventos a stdout mediante logging.
#
# Uso básico
# -----------
# from services.llm_adapter.client import LLMClient
# llm = LLMClient()
# text = await llm.generate("Hola")
#
# Parametrización
# ---------------
# - Variables de entorno (leer desde services.llm_adapter.settings):
#   LLM_MODEL_PATH, LLM_MAX_TOKENS, LLM_TEMPERATURE, LLM_TOP_P, LLM_CONTEXT_WINDOW
# - Modelo por defecto: scripts/export_webchatbot_env.sh intenta autodetectar un .gguf en ./modelos/
# - Instalación backend: pip install llama-cpp-python (o make install-rag)
#
# Consideraciones
# ---------------
# - Maneja excepciones y cae en PLACEHOLDER_REPLY si llama.cpp no está disponible
#   o el modelo no carga.
# - No implementa streaming; para ello habría que usar create_chat_completion/stream=True
#   y adaptar el frontend/API.
# - Loggers: INFO/WARN/ERROR/EXCEPTION van a stdout (config del proceso Uvicorn).
