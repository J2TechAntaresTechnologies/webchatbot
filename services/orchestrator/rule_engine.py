"""Motor simple de reglas para respuestas inmediatas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from services.orchestrator.types import ResponseSource
from services.orchestrator.text_utils import normalize_text


@dataclass(frozen=True)
class Rule:
    """Regla basada en coincidencia de palabras clave."""

    keywords: Sequence[str]
    response: str
    source: ResponseSource = "faq"

    def matches(self, normalized_text: str) -> bool:
        return all(keyword in normalized_text for keyword in self.keywords)


class RuleBasedResponder:
    """Motor mínimo de reglas definidas en DEFAULT_RULES."""

    def __init__(self, rules: Sequence[Rule] | None = None) -> None:
        self.rules: Sequence[Rule] = rules or DEFAULT_RULES

    async def get_response(self, message: str) -> tuple[str, ResponseSource] | None:
        normalized = normalize_text(message)
        for rule in self.rules:
            if rule.matches(normalized):
                return rule.response, rule.source
        return None


DEFAULT_RULES: Sequence[Rule] = (
    Rule(
        keywords=("horario", "atencion"),
        response=(
            "Nuestros horarios de atención al público son de lunes a viernes de 9 a 17 hs. "
            "Los sábados abrimos de 9 a 13 hs para trámites rápidos."
        ),
    ),
    Rule(
        keywords=("pag", "impuest"),
        response=(
            "Podés pagar tus impuestos municipales desde la web oficial en Trámites > Pagos. "
            "Aceptamos tarjetas, débito automático y pagos en entidades adheridas."
        ),
    ),
    Rule(
        keywords=("turno",),
        response="Ingresá en turnos.municipio.gob para solicitar o reprogramar tu turno municipal.",
    ),
    Rule(
        keywords=("contacto",),
        response="Podés llamar al 0800-123-4567 o escribir a atencion@municipio.gob de 8 a 20 hs.",
    ),
    Rule(
        keywords=("reclamo",),
        response="Usá la app Municipalidad Cerca o acercate a Atención Vecinal para cargar tu reclamo.",
    ),
    Rule(
        keywords=("hola",),
        response="¡Hola! ¿En qué puedo ayudarte hoy?",
        source="fallback",
    ),
    Rule(
        keywords=("ayuda",),
        response=(
            "Podés navegar con estas opciones:\n"
            "1. Conocer quiénes somos y cómo trabajamos (respondé 'opcion 1').\n"
            "2. Saber qué hace este chatbot y qué cubre (respondé 'opcion 2').\n"
            "3. Ver canales de contacto con el municipio (respondé 'opcion 3').\n"
            "4. Revisar trámites y servicios digitales disponibles (respondé 'opcion 4').\n"
            "Escribí el número u opción que prefieras."
        ),
        source="fallback",
    ),
    Rule(
        keywords=("opcion", "1"),
        response=(
            "Somos el equipo de Atención Digital del municipio, con especialistas en gestión de trámites, "
            "participación ciudadana y tecnología cívica. Trabajamos junto a las áreas de Atención Vecinal "
            "para darte respuestas claras y actualizadas."
        ),
    ),
    Rule(
        keywords=("1",),
        response=(
            "Somos el equipo de Atención Digital del municipio, con especialistas en gestión de trámites, "
            "participación ciudadana y tecnología cívica. Trabajamos junto a las áreas de Atención Vecinal "
            "para darte respuestas claras y actualizadas."
        ),
    ),
    Rule(
        keywords=("opcion", "2"),
        response=(
            "Este chatbot combina respuestas oficiales, búsquedas en la base de conocimiento municipal y un modelo LLM "
            "moderado. Puede orientarte con horarios, trámites frecuentes, normativa vigente y derivarte a una persona si es necesario."
        ),
    ),
    Rule(
        keywords=("2",),
        response=(
            "Este chatbot combina respuestas oficiales, búsquedas en la base de conocimiento municipal y un modelo LLM "
            "moderado. Puede orientarte con horarios, trámites frecuentes, normativa vigente y derivarte a una persona si es necesario."
        ),
    ),
    Rule(
        keywords=("opcion", "3"),
        response="Podés comunicarte al 0800-123-4567 de 8 a 20 hs o escribir a atencion@municipio.gob. También atendemos por WhatsApp al +54 9 11 5555-0000.",
    ),
    Rule(
        keywords=("3",),
        response="Podés comunicarte al 0800-123-4567 de 8 a 20 hs o escribir a atencion@municipio.gob. También atendemos por WhatsApp al +54 9 11 5555-0000.",
    ),
    Rule(
        keywords=("opcion", "4"),
        response=(
            "Disponés de turnos online, pagos de tasas, reclamos, consulta de ordenanzas y seguimiento de expedientes "
            "desde tramites.municipio.gob. También podés descargar comprobantes y pedir certificados digitales."
        ),
    ),
    Rule(
        keywords=("4",),
        response=(
            "Disponés de turnos online, pagos de tasas, reclamos, consulta de ordenanzas y seguimiento de expedientes "
            "desde tramites.municipio.gob. También podés descargar comprobantes y pedir certificados digitales."
        ),
    ),
    Rule(
        keywords=("gracia",),
        response="¡Gracias a vos! ¿Te ayudo con algo más?",
        source="fallback",
    ),
)

# ================================================================
# Guía de uso, parametrización e impacto (Motor de Reglas)
# ================================================================
#
# ¿Qué hace?
# -----------
# Responde inmediatamente a consultas que contengan ciertas palabras clave
# (match AND) en el texto normalizado (minúsculas, sin tildes). Devuelve
# (respuesta, source) donde source suele ser "faq" o "fallback".
#
# Uso básico
# -----------
# from services.orchestrator.rule_engine import RuleBasedResponder, Rule
# rules = [Rule(keywords=("horario","atencion"), response="..."),]
# responder = RuleBasedResponder(rules)
# match = await responder.get_response("¿Cuál es el horario de atención?")
# if match: reply, source = match
#
# Parametrización
# ---------------
# - Constructor acepta una lista de Rule personalizadas. Si no se pasa, usa DEFAULT_RULES.
# - Coincidencia: todas las keywords deben aparecer en el texto normalizado.
#   Usar raíces ("pag", "impuest") mejora recall ante variaciones.
# - "source": permite marcar respuestas como "faq" o "fallback" para trazabilidad.
# - Orden de reglas: se itera en orden; la primera coincidencia gana.
#
# Impacto en el bot
# -----------------
# - Si el IntentClassifier detecta "faq"/"smalltalk" y use_rules=True en settings,
#   el orquestador consultará este motor. Si hay match, responde sin invocar RAG ni LLM.
# - A mayor cobertura y calidad de reglas, menor latencia y menor costo en LLM.
#
# Buenas prácticas
# ----------------
# - Mantener respuestas oficiales y actualizadas. Evitar sobre-especificar keywords.
# - Alinear las reglas con los intents esperados y la base de conocimiento para evitar
#   inconsistencias.
# - Cubrir con tests frases de regresión frecuentes.
