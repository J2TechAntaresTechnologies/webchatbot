"""Lógica principal del orquestador."""

from __future__ import annotations

from services.orchestrator import schema
from services.llm_adapter.client import LLMClient
from services.orchestrator.intent_classifier import IntentClassifier
from services.orchestrator.rule_engine import RuleBasedResponder
from services.orchestrator.types import (
    IntentPrediction,
    RagResponderProtocol,
    ResponseSource,
)
from services.orchestrator.rag import SimpleRagResponder, load_default_entries
from services.chatbots.models import load_settings


class ChatOrchestrator:
    """Selecciona la fuente de respuesta adecuada."""

    def __init__(self) -> None:
        self._rules = RuleBasedResponder()
        self._classifier = IntentClassifier()
        self._llm = LLMClient()
        self._rag: RagResponderProtocol | None = None
        self._bootstrap_rag()

    async def respond(self, request: schema.ChatRequest) -> schema.ChatResponse:
        # Determinar bot y cargar configuración persistente
        channel = (request.channel or "").lower()
        bot_id = request.bot_id or ("mar2" if channel in {"mar2", "free"} else "municipal")
        settings = load_settings(bot_id, channel=channel)

        # Helper para inyectar pre-prompts de configuración
        def compose_with_preprompts(text: str) -> str:
            pre = [p.strip() for p in (getattr(settings, "pre_prompts", []) or []) if p and p.strip()]
            if not pre:
                return text
            instructions = "\n".join(f"- {p}" for p in pre)
            return (
                "Seguí estas instrucciones al responder:\n"
                f"{instructions}\n\n"
                f"{text}"
            )

        # Modo conversación libre (sin menú ni reglas): canal mar2/free
        if channel in {"mar2", "free"}:
            generated = await self._llm.generate(
                compose_with_preprompts(request.message),
                temperature=settings.generation.temperature,
                top_p=settings.generation.top_p,
                max_tokens=settings.generation.max_tokens,
            )
            return self._build_response(request, generated, "llm")

        prediction = await self._classifier.classify(request.message)

        if prediction.intent == "handoff":
            return self._build_response(
                request,
                "Te derivo con un agente humano para poder ayudarte mejor.",
                "fallback",
                escalated=True,
            )

        if settings.features.use_rules and (reply := await self._try_rules(request, prediction)):
            return reply

        if settings.features.use_rag and (reply := await self._try_rag(request, prediction)):
            return reply

        return await self._fallback(request, settings, compose_with_preprompts)

    @staticmethod
    def _build_response(
        request: schema.ChatRequest,
        reply: str,
        source: ResponseSource,
        escalated: bool = False,
    ) -> schema.ChatResponse:
        return schema.ChatResponse(
            session_id=request.session_id,
            reply=reply,
            source=source,
            escalated=escalated,
        )

    async def _try_rules(
        self, request: schema.ChatRequest, prediction: IntentPrediction
    ) -> schema.ChatResponse | None:
        if prediction.intent not in {"faq", "smalltalk"}:
            return None
        match = await self._rules.get_response(request.message)
        if not match:
            return None
        reply, source = match
        return self._build_response(request, reply, source)

    async def _try_rag(
        self, request: schema.ChatRequest, prediction: IntentPrediction
    ) -> schema.ChatResponse | None:
        if prediction.intent != "rag" or self._rag is None:
            return None
        reply = await self._rag.search(request.message)
        if reply is None:
            return None
        return self._build_response(request, reply, "rag")

    async def _fallback(self, request: schema.ChatRequest, settings=None, compose=None) -> schema.ChatResponse:
        if settings is not None:
            generated = await self._llm.generate(
                (compose(request.message) if callable(compose) else request.message),
                temperature=settings.generation.temperature,
                top_p=settings.generation.top_p,
                max_tokens=settings.generation.max_tokens,
            )
        else:
            generated = await self._llm.generate(request.message)
        return self._build_response(request, generated, "llm")

    def attach_rag(self, rag_responder: RagResponderProtocol) -> None:
        """Permite inyectar un componente RAG conforme al protocolo."""

        self._rag = rag_responder

    def _bootstrap_rag(self) -> None:
        try:
            entries = load_default_entries()
        except FileNotFoundError:
            return
        if entries:
            self.attach_rag(SimpleRagResponder(entries))

# ================================================================
# Guía de uso, parametrización e impacto (Orquestador)
# ================================================================
#
# ¿Qué hace?
# -----------
# Selecciona la fuente de respuesta según el mensaje y la configuración
# del bot/canal: Reglas/FAQ → RAG → LLM (con pre_prompts). Detecta
# handoff y devuelve una respuesta de derivación cuando corresponde.
#
# Uso básico
# -----------
# from services.orchestrator.service import ChatOrchestrator
# from services.orchestrator.schema import ChatRequest
# orch = ChatOrchestrator()
# resp = await orch.respond(ChatRequest(session_id="s1", message="Horario de atención", channel="web", bot_id="municipal"))
# # resp.reply, resp.source ("faq"|"rag"|"llm"|"fallback"), resp.escalated
#
# Parametrización (ajustes que afectan el flujo)
# ---------------------------------------------
# - Bot settings (persistentes por bot):
#   * generation: temperature/top_p/max_tokens → se pasan al LLM.
#   * features: use_rules/use_rag → habilitan o deshabilitan esas fases.
#   * pre_prompts: lista de instrucciones que se anteponen al mensaje del usuario.
#   Carga: services.chatbots.models.load_settings(bot_id, channel)
#   Persistencia: chatbots/<id>/settings.json (vía API o portal).
# - Canal/bot_id:
#   * channel "mar2"|"free" → conversación libre (salta reglas y RAG, usa LLM directo).
#   * channel "web" (u otros) → aplica flujo completo.
#   * Si no se envía bot_id, se infiere: mar2 para canal libre, municipal si no.
#
# Impacto y consideraciones
# -------------------------
# - Activar reglas y RAG reduce llamadas al LLM y mejora precisión en dominios cubiertos.
# - pre_prompts condiciona estilo/rol/políticas del LLM cuando se invoca.
# - No guarda estado de conversación (stateless). Si necesitás memoria, extender para
#   recuperar últimos turnos y pasarlos al LLM.
# - Concurrencia: una única instancia del orquestador se reutiliza; componentes son
#   inmutables salvo el cliente LLM.
#
# Puntos de extensión
# -------------------
# - attach_rag(rag): inyectar un conector RAG que cumpla el protocolo.
# - Sustituir IntentClassifier o RuleBasedResponder por variantes propias.
# - Reemplazar LLMClient por otro backend (OpenAI/vertex) manteniendo generate().
#
# Pruebas
# -------
# - tests/unit/test_orchestrator_basic.py valida caminos happy-path de reglas, RAG y fallback.
