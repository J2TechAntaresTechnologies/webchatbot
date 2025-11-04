"""Routers para endpoints de chat."""

from fastapi import APIRouter

from services.orchestrator import schema
from services.orchestrator.service import ChatOrchestrator

router = APIRouter()
_orchestrator = ChatOrchestrator()


@router.post("/message", response_model=schema.ChatResponse)
async def handle_message(payload: schema.ChatRequest) -> schema.ChatResponse:
    return await _orchestrator.respond(payload)

# ================================================================
# Guía de uso (API de chat)
# ================================================================
#
# Endpoint
# --------
# POST /chat/message
# Body (JSON): {"session_id": str, "message": str, "channel": str = "web", "bot_id": str | null}
# Response: {"session_id": str, "reply": str, "source": "faq|rag|llm|fallback", "escalated": bool}
#
# Ejemplo
# -------
# curl -sS -X POST http://127.0.0.1:8000/chat/message \
#   -H 'Content-Type: application/json' \
#   -d '{"session_id":"web-local","message":"Horario de atención","channel":"web","bot_id":"municipal"}' | jq .
#
# Consideraciones
# ---------------
# - Stateless: no almacena historial; cada request es independiente.
# - El orquestador usa settings del bot/canal para decidir reglas/RAG/LLM y pre_prompts.
# - Para streaming, se requeriría un endpoint alternativo (SSE/WebSocket) no implementado aquí.
