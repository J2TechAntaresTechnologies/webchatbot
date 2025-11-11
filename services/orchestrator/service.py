"""Lógica principal del orquestador."""

from __future__ import annotations

from services.orchestrator import schema
import random
from services.llm_adapter.client import LLMClient
from services.orchestrator.intent_classifier import IntentClassifier
from services.orchestrator.rule_engine import RuleBasedResponder, Rule
from services.orchestrator.types import (
    IntentPrediction,
    RagResponderProtocol,
    ResponseSource,
)
import os
from services.orchestrator.rag import SimpleRagResponder, load_default_entries, load_text_dir_entries, KnowledgeEntry
from pathlib import Path
from services.chatbots.models import load_settings


class ChatOrchestrator:
    """Selecciona la fuente de respuesta adecuada."""

    def __init__(self) -> None:
        self._rules = RuleBasedResponder()
        self._classifier = IntentClassifier()
        self._llm = LLMClient()
        self._rag: RagResponderProtocol | None = None
        self._rag_entries: list[KnowledgeEntry] | None = None
        self._rag_cache: dict[float, RagResponderProtocol] = {}
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

        # Reglas: si hay match responde; si no hay match y está activado
        # features.use_generic_no_match, devuelve un mensaje genérico orientando
        # a reformular (sin pasar por RAG/LLM para intents faq/smalltalk).
        if settings.features.use_rules and (reply := await self._try_rules(request, prediction, settings)):
            return reply

        if settings.features.use_rag and (reply := await self._try_rag(request, prediction, settings)):
            return reply

        # Si no hubo match y el intent es "unknown", y está habilitada la
        # respuesta genérica, devolverla (evita ir al LLM para entradas vagas).
        if getattr(settings.features, "use_generic_no_match", False) and prediction.intent == "unknown":
            replies = [
                p.strip()
                for p in (getattr(settings, "no_match_replies", []) or [])
                if isinstance(p, str) and p.strip()
            ]
            if replies:
                pick = getattr(settings, "no_match_pick", "first")
                text = random.choice(replies) if pick == "random" else replies[0]
            else:
                text = (
                    "No pude comprender tu consulta. Intentá reformularla en pocas palabras o escribí 'ayuda' para ver opciones."
                )
            return self._build_response(request, text, "fallback")

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
        self, request: schema.ChatRequest, prediction: IntentPrediction, settings=None
    ) -> schema.ChatResponse | None:
        if prediction.intent not in {"faq", "smalltalk"}:
            return None
        # Si hay settings, combinar reglas por defecto con personalizadas según enable_default_rules.
        responder = self._rules
        if settings is not None:
            try:
                custom_rules_data = getattr(settings, "rules", []) or []
                custom_rules: list[Rule] = []
                for rc in custom_rules_data:
                    # rc puede ser dict o RuleConfig; acceder de forma segura
                    keywords = list(getattr(rc, "keywords", []) or (rc.get("keywords", []) if isinstance(rc, dict) else []))
                    response = getattr(rc, "response", None) if not isinstance(rc, dict) else rc.get("response")
                    source = getattr(rc, "source", "faq") if not isinstance(rc, dict) else rc.get("source", "faq")
                    enabled = getattr(rc, "enabled", True) if not isinstance(rc, dict) else rc.get("enabled", True)
                    min_matches = getattr(rc, "min_matches", None) if not isinstance(rc, dict) else rc.get("min_matches")
                    if enabled and keywords and isinstance(response, str) and response.strip():
                        # Normalizar min_matches (entero positivo) si se provee
                        mm = None
                        try:
                            if min_matches is not None:
                                mm_val = int(min_matches)
                                mm = mm_val if mm_val > 0 else None
                        except Exception:
                            mm = None
                        custom_rules.append(
                            Rule(
                                keywords=tuple(keywords),
                                response=response.strip(),
                                source=("fallback" if source == "fallback" else "faq"),
                                min_matches=mm,
                            )
                        )
                rules: list[Rule] = []
                # Priorizar reglas personalizadas (más específicas) por delante de las default
                rules.extend(custom_rules)
                if getattr(settings.features, "enable_default_rules", True):
                    rules.extend(self._rules.rules)
                if rules:
                    responder = RuleBasedResponder(rules)
            except Exception:
                # En caso de estructura inesperada, continuar con defaults
                responder = self._rules
        match = await responder.get_response(request.message)
        if not match:
            # Si no hay coincidencia de reglas y el bot lo permite, responder
            # con un genérico de “no comprendo; intentá reformular/ayuda”.
            if settings is not None and getattr(settings.features, "use_generic_no_match", False):
                replies = [
                    p.strip()
                    for p in (getattr(settings, "no_match_replies", []) or [])
                    if isinstance(p, str) and p.strip()
                ]
                if replies:
                    pick = getattr(settings, "no_match_pick", "first")
                    text = random.choice(replies) if pick == "random" else replies[0]
                else:
                    text = (
                        "No pude comprender tu consulta. Intentá reformularla en pocas palabras o escribí 'ayuda' para ver opciones."
                    )
                return self._build_response(request, text, "fallback")
            return None
        reply, source = match
        return self._build_response(request, reply, source)

    async def _try_rag(
        self, request: schema.ChatRequest, prediction: IntentPrediction, settings=None
    ) -> schema.ChatResponse | None:
        if prediction.intent != "rag" or self._rag is None:
            return None
        # Seleccionar RAG según threshold configurado
        responder = self._rag
        try:
            thr = float(getattr(settings, "rag_threshold", 0.28)) if settings is not None else 0.28
        except Exception:
            thr = 0.28
        if self._rag_entries and isinstance(thr, float):
            # Cache por threshold para evitar recomputar embeddings por request
            cached = self._rag_cache.get(thr)
            if cached is None:
                self._rag_cache[thr] = SimpleRagResponder(self._rag_entries, threshold=thr)
                cached = self._rag_cache[thr]
            responder = cached
        reply = await responder.search(request.message)
        if reply is None:
            return None
        return self._build_response(request, reply, "rag")

    async def _fallback(self, request: schema.ChatRequest, settings=None, compose=None) -> schema.ChatResponse:
        # Modo "grounded only": no invoca LLM si está habilitado por variable de entorno
        grounded_only = os.getenv("WEBCHATBOT_GROUNDED_ONLY", "0").lower() not in {"", "0", "false", "no"}
        if grounded_only:
            # Abstenerse de inventar si no hubo reglas ni RAG
            text = (
                "Por ahora no tengo información precisa sobre esto en nuestros datos. "
                "Probá con otra frase o escribí 'ayuda' para ver opciones."
            )
            return self._build_response(request, text, "fallback")
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
            entries = list(load_default_entries())
        except FileNotFoundError:
            entries = []
        # Ampliar KB con textos curatoriales (munivilladata) si existe
        try:
            root = Path(__file__).resolve().parents[2]
            extra_dir_env = os.getenv("WEBCHATBOT_TEXT_KB_DIR", "").strip()
            extra_dir = Path(extra_dir_env) if extra_dir_env else (root / "00relevamientos_j2" / "munivilladata")
            extra_entries = load_text_dir_entries(extra_dir)
            if extra_entries:
                entries.extend(extra_entries)
        except Exception:
            pass
        if entries:
            # Guardar entradas para construir variantes por threshold
            self._rag_entries = list(entries)
            default_thr = 0.28
            responder = SimpleRagResponder(self._rag_entries, threshold=default_thr)
            self._rag_cache[default_thr] = responder
            self.attach_rag(responder)

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
