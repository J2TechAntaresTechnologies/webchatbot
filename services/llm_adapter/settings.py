"""Configuración para el adaptador LLM."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """Lee configuración del LLM desde variables de entorno."""

    model_path: Path | None = Field(default=None, alias="LLM_MODEL_PATH")
    max_tokens: int = Field(default=256, alias="LLM_MAX_TOKENS")
    temperature: float = Field(default=0.7, alias="LLM_TEMPERATURE")
    top_p: float = Field(default=0.9, alias="LLM_TOP_P")
    context_window: int = Field(default=2048, alias="LLM_CONTEXT_WINDOW")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    @property
    def has_model_path(self) -> bool:
        return self.model_path is not None

# ================================================================
# Guía de uso (Settings del LLM)
# ================================================================
#
# Variables de entorno soportadas
# -------------------------------
# - LLM_MODEL_PATH: ruta al archivo .gguf.
# - LLM_MAX_TOKENS: tokens máximos por respuesta (default 256).
# - LLM_TEMPERATURE: aleatoriedad (default 0.7).
# - LLM_TOP_P: nucleus sampling (default 0.9).
# - LLM_CONTEXT_WINDOW: tamaño de contexto (default 2048).
#
# Fuente de configuración
# -----------------------
# - .env en la raíz (si existe) y entorno del proceso (pydantic-settings).
# - scripts/export_webchatbot_env.sh exporta valores convenientes al activar el venv.
#
# Tips
# ----
# - Usar rutas absolutas para LLM_MODEL_PATH.
# - Verificar compatibilidad de la versión de llama-cpp-python con el modelo elegido.
