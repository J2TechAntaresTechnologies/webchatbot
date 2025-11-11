"""Motor simple de reglas para respuestas inmediatas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from services.orchestrator.types import ResponseSource
from services.orchestrator.text_utils import normalize_text


@dataclass(frozen=True)
class Rule:
    """Regla basada en coincidencia de palabras clave.

    - keywords: stems/raíces a buscar (match por subcadena tras normalizar).
    - response: texto de respuesta.
    - source: `faq` o `fallback` para trazabilidad.
    - min_matches: cantidad mínima de keywords que deben aparecer. Si es None,
      se exige match de todas (AND). Con min_matches < len(keywords) se logra
      un comportamiento más "suave" (k-de-n) para consultas variadas.
    """

    keywords: Sequence[str]
    response: str
    source: ResponseSource = "faq"
    min_matches: int | None = None

    def matches(self, normalized_text: str) -> bool:
        if not self.keywords:
            return False
        required = len(self.keywords) if self.min_matches is None else max(1, int(self.min_matches))
        hits = sum(1 for kw in self.keywords if kw in normalized_text)
        return hits >= required


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
    # Consulta genérica sobre cómo pagar (conservadora): coincide con "como" y "pag".
    # Devuelve la misma respuesta oficial de pagos.
    Rule(
        keywords=("como", "pag"),
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
    # OR lógico entre "ayuda" y "menu" implementado duplicando la regla
    Rule(
        keywords=("ayuda",),
        response=(
            "Menú principal (escribí una frase o palabra clave):\n"
            "1) Bienestar y Salud → amsa, cic, consumos, punto violeta, discapacidad, dengue\n"
            "2) Educación y Juventud → juventud, deporte, congreso cer, economía social\n"
            "3) Trámites y Gestiones → trámite online, turno licencia, proveedores\n"
            "4) Cultura, Turismo y Ambiente → agenda cultural, turismo, villa más limpia\n"
            "5) Desarrollo Urbano y Comercio → obras privadas, planificación, comercio\n"
            "6) Información y Contacto → contacto, emergencias, horarios\n"
            "Sugerencia: por ejemplo, escribí ‘turno licencia’ o ‘punto violeta’."
        ),
        source="fallback",
    ),
    Rule(
        keywords=("menu",),
        response=(
            "Menú principal (escribí una frase o palabra clave):\n"
            "1) Bienestar y Salud → amsa, cic, consumos, punto violeta, discapacidad, dengue\n"
            "2) Educación y Juventud → juventud, deporte, congreso cer, economía social\n"
            "3) Trámites y Gestiones → trámite online, turno licencia, proveedores\n"
            "4) Cultura, Turismo y Ambiente → agenda cultural, turismo, villa más limpia\n"
            "5) Desarrollo Urbano y Comercio → obras privadas, planificación, comercio\n"
            "6) Información y Contacto → contacto, emergencias, horarios\n"
            "Sugerencia: por ejemplo, escribí ‘turno licencia’ o ‘punto violeta’."
        ),
        source="fallback",
    ),
    # Regla "suave" para consultas sobre trámites y servicios digitales:
    # Usa stems y requiere al menos 2 coincidencias para reducir falsos positivos.
    Rule(
        keywords=("tramit", "servici", "digital"),
        response=(
            "Disponés de turnos online, pagos de tasas, reclamos, consulta de ordenanzas y seguimiento de expedientes "
            "desde tramites.municipio.gob. También podés descargar comprobantes y pedir certificados digitales."
        ),
        min_matches=2,
    ),
    # Quiénes somos (conservadora): cubre "quiénes somos" y "quiénes son".
    Rule(
        keywords=("quien", "somos"),
        response=(
            "Somos el equipo de Atención Digital del municipio, con especialistas en gestión de trámites, "
            "participación ciudadana y tecnología cívica. Trabajamos junto a las áreas de Atención Vecinal "
            "para darte respuestas claras y actualizadas."
        ),
    ),
    Rule(
        keywords=("quien", "son"),
        response=(
            "Somos el equipo de Atención Digital del municipio, con especialistas en gestión de trámites, "
            "participación ciudadana y tecnología cívica. Trabajamos junto a las áreas de Atención Vecinal "
            "para darte respuestas claras y actualizadas."
        ),
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
