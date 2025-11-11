"""Modelos y utilidades para configuración de chatbots."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

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
    use_generic_no_match: bool = Field(
        False,
        description=(
            "Responder con un mensaje genérico predefinido cuando no haya coincidencias en reglas/RAG y el intent no derive a handoff."
        ),
    )
    enable_default_rules: bool = Field(
        True,
        description="Incluir el set de reglas por defecto del motor (DEFAULT_RULES) además de las reglas personalizadas.",
    )


class RuleConfig(BaseModel):
    """Regla configurable desde settings.

    - enabled: si la regla está activa.
    - keywords: lista de palabras clave/stems (match AND).
    - response: texto a devolver si coincide.
    - source: etiqueta de origen (faq|fallback). Se usa para trazabilidad.
    """

    enabled: bool = Field(True)
    keywords: list[str] = Field(default_factory=list)
    response: str = Field("")
    source: Literal["faq", "fallback"] = Field("faq")


class MenuItem(BaseModel):
    label: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class BotSettings(BaseModel):
    generation: GenerationSettings = Field(default_factory=GenerationSettings)
    features: FeatureToggles = Field(default_factory=FeatureToggles)
    rag_threshold: float = Field(0.28, ge=0.0, le=1.0, description="Umbral de similitud para RAG [0,1]")
    grounded_only: bool = Field(
        False,
        description=(
            "Si es True, el orquestador no invoca LLM como fallback: responde solo con Reglas y RAG (abstiene si no hay match)."
        ),
    )
    allowed_domains: list[str] = Field(
        default_factory=list,
        description="Lista blanca de dominios válidos para enlaces en respuestas (vacío = permitir todos)",
    )
    help_template: str = Field(
        default="",
        description="Plantilla de ayuda/menu (si está vacía, se usan las reglas por defecto)",
    )
    menu_suggestions: list[MenuItem] = Field(default_factory=list)
    pre_prompts: list[str] = Field(default_factory=list, description="Instrucciones iniciales a inyectar antes del mensaje del usuario")
    no_match_replies: list[str] = Field(
        default_factory=list,
        description=(
            "Respuestas genéricas a usar cuando no hay match y use_generic_no_match=True. Se usa la primera disponible."
        ),
    )
    no_match_pick: Literal["first", "random"] = Field(
        "first",
        description="Estrategia para elegir la respuesta genérica: 'first' o 'random'",
    )
    rules: list[RuleConfig] = Field(
        default_factory=list,
        description="Lista de reglas personalizadas a sumar (o reemplazar) al motor de reglas.",
    )

    def clamped(self) -> "BotSettings":
        return BotSettings(
            generation=self.generation.clamped(),
            features=self.features,
            rag_threshold=min(max(float(getattr(self, "rag_threshold", 0.28)), 0.0), 1.0),
            grounded_only=bool(getattr(self, "grounded_only", False)),
            allowed_domains=[d.strip() for d in (getattr(self, "allowed_domains", []) or []) if isinstance(d, str) and d.strip()],
            help_template=str(getattr(self, "help_template", "") or ""),
            menu_suggestions=self.menu_suggestions,
            pre_prompts=[p for p in self.pre_prompts if isinstance(p, str) and p.strip() != ""],
            no_match_replies=[p.strip() for p in (self.no_match_replies or []) if isinstance(p, str) and p.strip() != ""],
            no_match_pick=(self.no_match_pick if getattr(self, "no_match_pick", "first") in {"first", "random"} else "first"),
            rules=[
                RuleConfig.model_validate(r)
                for r in (getattr(self, "rules", []) or [])
                if isinstance(r, (dict, RuleConfig))
            ],
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
            features=FeatureToggles(use_rules=False, use_rag=False, use_generic_no_match=False, enable_default_rules=False),
            rag_threshold=0.28,
            menu_suggestions=[],
            pre_prompts=[],
            no_match_replies=[
                "No pude comprender tu consulta. Escribí 'ayuda' para ver opciones o contame en pocas palabras qué necesitás.",
            ],
            no_match_pick="first",
            rules=[],
        )
    # Por defecto (municipal web guiado)
    return BotSettings(
        generation=GenerationSettings(temperature=0.7, top_p=0.9, max_tokens=200),
        features=FeatureToggles(use_rules=True, use_rag=True, use_generic_no_match=False, enable_default_rules=True),
        rag_threshold=0.28,
        grounded_only=True,
        allowed_domains=[
            "municipio.gob",
            "municipio.gob.ar",
            "tramites.municipio.gob",
            "proveedores.municipio.gob",
            "salud.municipio.gob",
            "genero.municipio.gob",
            "educacion.municipio.gob",
            "turismo.municipio.gob",
            "cultura.municipio.gob",
            "ambiente.municipio.gob",
        ],
        help_template=(
            "Menú principal (escribí una frase o palabra clave):\n"
            "1) Bienestar y Salud → amsa, cic, consumos, punto violeta, discapacidad, dengue\n"
            "2) Educación y Juventud → juventud, deporte, congreso cer, economía social\n"
            "3) Trámites y Gestiones → trámite online, turno licencia, proveedores\n"
            "4) Cultura, Turismo y Ambiente → agenda cultural, turismo, villa más limpia\n"
            "5) Desarrollo Urbano y Comercio → obras privadas, planificación, comercio\n"
            "6) Información y Contacto → contacto, emergencias, horarios\n"
            "Sugerencia: por ejemplo, escribí ‘turno licencia’ o ‘punto violeta’."
        ),
        menu_suggestions=[
            MenuItem(label="Trámites online", message="¿Qué trámites puedo hacer online?"),
            MenuItem(label="Turnos licencia de conducir", message="Quiero sacar un turno para licencia de conducir"),
            MenuItem(label="Inscripción de proveedores", message="¿Cómo me inscribo como proveedor municipal?"),
            MenuItem(label="Punto Violeta", message="¿Qué es el Punto Violeta y dónde está?"),
            MenuItem(label="Consumos problemáticos", message="Necesito ayuda por consumos problemáticos"),
            MenuItem(label="Certificado de discapacidad", message="¿Cómo tramito el Certificado de Discapacidad?"),
            MenuItem(label="Cultura y agenda", message="¿Qué actividades culturales hay este mes?"),
            MenuItem(label="Turismo", message="¿Qué atractivos turísticos tiene la ciudad?"),
            MenuItem(label="Ambiente (Villa Más Limpia)", message="¿Cómo es la separación y recolección?"),
            MenuItem(label="Economía social", message="¿Qué apoyo brinda Economía Social?"),
            MenuItem(label="Obras privadas", message="¿Cómo son los trámites de obras privadas?"),
            MenuItem(label="Contacto y emergencias", message="Necesito números de contacto y emergencias"),
            MenuItem(label="Ayuda", message="ayuda"),
        ],
        pre_prompts=[
            "Responde con frases cortas y claras; usá viñetas cuando enumeres.",
            "Preferí fuentes oficiales y mencioná el área responsable cuando aplique.",
            "Ante emergencias: indicá 911 (Policía), 107 (Hospital), 100 (Bomberos).",
        ],
        no_match_replies=[],
        no_match_pick="first",
        rules=[],
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
