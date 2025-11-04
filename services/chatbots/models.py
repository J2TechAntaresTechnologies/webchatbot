"""Modelos y utilidades para configuración de chatbots."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, PositiveInt, field_validator


class GenerationSettings(BaseModel):
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperatura de muestreo")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Top-p nucleus sampling")
    max_tokens: PositiveInt = Field(256, description="Límite de tokens de salida")

    def clamped(self) -> "GenerationSettings":
        # Pydantic ya valida límites, pero reforzamos por seguridad.
        t = min(max(self.temperature, 0.0), 2.0)
        p = min(max(self.top_p, 0.0), 1.0)
        m = max(int(self.max_tokens), 1)
        return GenerationSettings(temperature=t, top_p=p, max_tokens=m)


class FeatureToggles(BaseModel):
    use_rules: bool = Field(True, description="Usar motor de reglas/FAQ")
    use_rag: bool = Field(True, description="Usar RAG si disponible")


class MenuItem(BaseModel):
    label: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class BotSettings(BaseModel):
    generation: GenerationSettings = Field(default_factory=GenerationSettings)
    features: FeatureToggles = Field(default_factory=FeatureToggles)
    menu_suggestions: list[MenuItem] = Field(default_factory=list)
    pre_prompts: list[str] = Field(default_factory=list, description="Instrucciones iniciales a inyectar antes del mensaje del usuario")

    def clamped(self) -> "BotSettings":
        return BotSettings(
            generation=self.generation.clamped(),
            features=self.features,
            menu_suggestions=self.menu_suggestions,
            pre_prompts=[p for p in self.pre_prompts if isinstance(p, str) and p.strip() != ""],
        )


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def chatbots_dir() -> Path:
    return project_root() / "chatbots"


def bot_dir(bot_id: str) -> Path:
    return chatbots_dir() / bot_id


def settings_path(bot_id: str) -> Path:
    return bot_dir(bot_id) / "settings.json"


def defaults_for(bot_id: str, channel: str | None = None) -> BotSettings:
    # Baselines por variante conocidas
    if bot_id == "mar2" or (channel or "").lower() in {"mar2", "free"}:
        return BotSettings(
            generation=GenerationSettings(temperature=0.7, top_p=0.9, max_tokens=256),
            features=FeatureToggles(use_rules=False, use_rag=False),
            menu_suggestions=[],
            pre_prompts=[],
        )
    # Por defecto (municipal web guiado)
    return BotSettings(
        generation=GenerationSettings(temperature=0.7, top_p=0.9, max_tokens=256),
        features=FeatureToggles(use_rules=True, use_rag=True),
        menu_suggestions=[
            MenuItem(label="Pagar impuestos", message="¿Cómo pago mis impuestos?"),
            MenuItem(label="Sacar turno", message="Quiero sacar un turno"),
            MenuItem(label="Hacer reclamo", message="Quiero hacer un reclamo"),
            MenuItem(label="Ayuda", message="ayuda"),
        ],
        pre_prompts=[],
    )


def load_settings(bot_id: str, channel: str | None = None) -> BotSettings:
    p = settings_path(bot_id)
    if p.exists():
        try:
            data: dict[str, Any] = BotSettings.model_validate_json(p.read_text(encoding="utf-8")).model_dump()
            return BotSettings.model_validate(data).clamped()
        except Exception:
            # Si el archivo está corrupto, volvemos a defaults
            return defaults_for(bot_id, channel)
    return defaults_for(bot_id, channel)


def save_settings(bot_id: str, settings: BotSettings) -> None:
    d = bot_dir(bot_id)
    d.mkdir(parents=True, exist_ok=True)
    p = settings_path(bot_id)
    json_str = settings.clamped().model_dump_json(indent=2)
    p.write_text(json_str + "\n", encoding="utf-8")


def reset_settings(bot_id: str, channel: str | None = None) -> BotSettings:
    d = bot_dir(bot_id)
    d.mkdir(parents=True, exist_ok=True)
    defaults = defaults_for(bot_id, channel)
    save_settings(bot_id, defaults)
    return defaults

# ================================================================
# Guía de uso y parametrización (Settings de chatbots)
# ================================================================
#
# ¿Qué define?
# -------------
# - Esquema de configuración por bot: generación (temperature/top_p/max_tokens),
#   toggles de features (use_rules/use_rag), menú de sugerencias y pre_prompts.
# - Helpers de ruta/IO para persistir en chatbots/<id>/settings.json.
#
# Uso básico
# -----------
# from services.chatbots.models import load_settings, save_settings, reset_settings, BotSettings
# st = load_settings("municipal", channel="web")   # aplica defaults si no existe el archivo
# st.pre_prompts.append("Responde de forma clara y concisa")
# save_settings("municipal", st)                    # escribe chatbots/municipal/settings.json
# st2 = reset_settings("municipal", channel="web") # restablece defaults y devuelve
#
# Estructura JSON (ejemplo)
# -------------------------
# {
#   "generation": {"temperature": 0.7, "top_p": 0.9, "max_tokens": 256},
#   "features": {"use_rules": true, "use_rag": true},
#   "menu_suggestions": [{"label": "Pagar impuestos", "message": "¿Cómo pago mis impuestos?"}],
#   "pre_prompts": ["Responde con tono claro"]
# }
#
# Consideraciones
# ---------------
# - clamped(): asegura que valores numéricos respeten límites seguros.
# - defaults_for(): define defaults por bot/canal (mar2 desactiva reglas y RAG por defecto).
# - IO: los helpers crean directorios si hiciera falta; manejo básico de corrupción → vuelve a defaults.
