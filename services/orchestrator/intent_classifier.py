"""Clasificador heurístico simple de intents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from services.orchestrator.text_utils import normalize_text
from services.orchestrator.types import IntentName, IntentPrediction


@dataclass(frozen=True)
class IntentPattern:
    """Patrón de intent basado en palabras clave."""

    intent: IntentName
    keywords: Sequence[str]
    confidence: float = 0.6

    def matches(self, normalized_text: str) -> bool:
        return all(keyword in normalized_text for keyword in self.keywords)


class IntentClassifier:
    """Clasifica mensajes en intents básicos usando reglas heurísticas."""

    def __init__(self, patterns: Sequence[IntentPattern] | None = None) -> None:
        self.patterns: Sequence[IntentPattern] = patterns or DEFAULT_PATTERNS

    async def classify(self, message: str) -> IntentPrediction:
        normalized = normalize_text(message)
        for pattern in self.patterns:
            if pattern.matches(normalized):
                return IntentPrediction(intent=pattern.intent, confidence=pattern.confidence)
        return IntentPrediction(intent="unknown", confidence=0.0)


DEFAULT_PATTERNS: Sequence[IntentPattern] = (
    IntentPattern(intent="faq", keywords=("horario", "atencion"), confidence=0.9),
    IntentPattern(intent="faq", keywords=("pag", "impuest"), confidence=0.8),
    IntentPattern(intent="faq", keywords=("como", "pag"), confidence=0.7),
    IntentPattern(intent="faq", keywords=("quien", "somos"), confidence=0.7),
    IntentPattern(intent="faq", keywords=("quien", "son"), confidence=0.7),
    IntentPattern(intent="faq", keywords=("turno",), confidence=0.75),
    IntentPattern(intent="faq", keywords=("contacto",), confidence=0.75),
    IntentPattern(intent="faq", keywords=("reclamo",), confidence=0.7),
    IntentPattern(intent="smalltalk", keywords=("hola",), confidence=0.5),
    IntentPattern(intent="smalltalk", keywords=("ayuda",), confidence=0.5),
    IntentPattern(intent="smalltalk", keywords=("menu",), confidence=0.5),
    IntentPattern(intent="smalltalk", keywords=("gracia",), confidence=0.4),
    IntentPattern(intent="smalltalk", keywords=("opcion",), confidence=0.4),
    IntentPattern(intent="smalltalk", keywords=("1",), confidence=0.3),
    IntentPattern(intent="smalltalk", keywords=("2",), confidence=0.3),
    IntentPattern(intent="smalltalk", keywords=("3",), confidence=0.3),
    IntentPattern(intent="smalltalk", keywords=("4",), confidence=0.3),
    IntentPattern(intent="handoff", keywords=("hablar", "agente"), confidence=0.8),
    IntentPattern(intent="rag", keywords=("ordenanza",), confidence=0.6),
    IntentPattern(intent="rag", keywords=("normativa",), confidence=0.6),
    # Patrones RAG adicionales (stems) para habilitar búsquedas sobre permisos de poda/ambiente
    IntentPattern(intent="rag", keywords=("ambiente", "permis"), confidence=0.65),
    IntentPattern(intent="rag", keywords=("poda",), confidence=0.65),
    # Munivilla (servicios): encaminar consultas típicas a RAG
    IntentPattern(intent="rag", keywords=("licenc", "conduc"), confidence=0.65),
    IntentPattern(intent="rag", keywords=("proveedor", "inscrip"), confidence=0.65),
    IntentPattern(intent="rag", keywords=("discap", "certific"), confidence=0.65),
    IntentPattern(intent="rag", keywords=("genero", "violeta"), confidence=0.65),
    IntentPattern(intent="rag", keywords=("dengue",), confidence=0.65),
)

# ================================================================
# Guía de uso, parametrización e impacto (presets de ejemplo)
# ================================================================
#
# Uso básico
# -----------
# from services.orchestrator.intent_classifier import IntentClassifier
# clf = IntentClassifier()  # usa DEFAULT_PATTERNS (abajo)
# pred = await clf.classify("Necesito saber el horario de atención")
# # pred.intent -> "faq" | "rag" | "smalltalk" | "handoff" | "unknown"
# # pred.confidence -> float informativa (no se umbraliza en el orquestador)
#
# Parametrización
# ---------------
# - Podés inyectar tus propios patrones en el constructor:
#
#   from services.orchestrator.intent_classifier import IntentClassifier, IntentPattern
#   custom_patterns = (
#       IntentPattern(intent="faq", keywords=("horario", "atencion"), confidence=0.9),
#       IntentPattern(intent="rag", keywords=("ordenanza",), confidence=0.7),
#   )
#   clf = IntentClassifier(patterns=custom_patterns)
#
# - Coincidencia: cada patrón hace match si TODAS las palabras clave
#   aparecen como subcadenas en el texto normalizado (minúsculas, sin tildes).
#   Por eso se usan raíces ("pag", "impuest") para cubrir variaciones.
# - Orden importa: el clasificador revisa los patrones en orden y devuelve
#   el primero que coincide. Colocá primero los más específicos.
# - confidence: es un valor informativo que viaja con el IntentPrediction.
#   El orquestador no umbraliza actualmente por confidence; usa sólo intent.
#
# Impacto en el bot (flujo de orquestación)
# -----------------------------------------
# - intent="faq" o "smalltalk" → intenta responder con reglas (respuestas fijas).
# - intent="rag" → intenta búsqueda en la base (knowledge/faqs/municipal_faqs.json).
# - intent="handoff" → responde derivación a agente humano.
# - Si nada aplica, cae a LLM (con pre_prompts según settings del bot).
#
# Buenas prácticas
# ----------------
# - Usá stems/raíces de keywords para mayor recall ("recolec" en vez de "recolección").
# - Evitá keywords excesivamente generales que puedan capturar consultas que deberían
#   ir al LLM o a RAG.
# - Mantené los patrones alineados con el contenido real de `knowledge/*` y `rule_engine`.
# - Testeá con frases reales; ajustá orden y keywords hasta reducir falsos positivos.
#
# Presets de ejemplo
# ------------------
# 1) Municipal enriquecido (más cobertura RAG y trámites):
#
# MUNICIPAL_PRESET = (
#     IntentPattern(intent="faq", keywords=("horario", "atencion"), confidence=0.9),
#     IntentPattern(intent="faq", keywords=("turno",), confidence=0.8),
#     IntentPattern(intent="faq", keywords=("contacto",), confidence=0.75),
#     IntentPattern(intent="faq", keywords=("reclamo",), confidence=0.7),
#     IntentPattern(intent="rag", keywords=("ordenanza",), confidence=0.7),
#     IntentPattern(intent="rag", keywords=("normativa",), confidence=0.7),
#     IntentPattern(intent="rag", keywords=("libre", "deuda"), confidence=0.65),
#     IntentPattern(intent="rag", keywords=("expediente",), confidence=0.65),
#     IntentPattern(intent="rag", keywords=("habilit",), confidence=0.65),
#     IntentPattern(intent="rag", keywords=("poda",), confidence=0.65),
#     IntentPattern(intent="rag", keywords=("luminaria",), confidence=0.65),
#     IntentPattern(intent="rag", keywords=("recolec",), confidence=0.65),
#     IntentPattern(intent="smalltalk", keywords=("hola",), confidence=0.5),
#     IntentPattern(intent="smalltalk", keywords=("ayuda",), confidence=0.5),
#     IntentPattern(intent="handoff", keywords=("hablar", "agente"), confidence=0.8),
# )
#
# 2) MAR2 (modo libre): orientado a reducir capturas por reglas y dejar más al LLM.
#    Sugerencia: patrones mínimos (saludos/ayuda y handoff) y menos RAG.
#
# MAR2_PRESET = (
#     IntentPattern(intent="smalltalk", keywords=("hola",), confidence=0.4),
#     IntentPattern(intent="smalltalk", keywords=("ayuda",), confidence=0.4),
#     IntentPattern(intent="handoff", keywords=("hablar", "agente"), confidence=0.8),
# )
#
# Cómo usar un preset
# -------------------
# clf = IntentClassifier(patterns=MUNICIPAL_PRESET)
# # o
# clf = IntentClassifier(patterns=MAR2_PRESET)
#
# Nota: Si combinás este archivo con cambios en `rule_engine.py` y `knowledge/faqs/*`,
# podrás alinear clasificación, reglas y cobertura de RAG para maximizar precisión
# y reducir llamadas innecesarias al LLM.
