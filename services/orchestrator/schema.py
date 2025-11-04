"""Modelos Pydantic para IO del orquestador."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Identificador único de sesión")
    message: str = Field(..., min_length=1, description="Mensaje del usuario")
    channel: str = Field("web", description="Canal (web, whatsapp, etc.)")
    bot_id: str | None = Field(None, description="Identificador de la variante de chatbot")


class ChatResponse(BaseModel):
    session_id: str = Field(..., description="Identificador correlacionado")
    reply: str = Field(..., description="Respuesta generada")
    source: str = Field(..., description="Origen de la respuesta (faq, rag, llm, fallback)")
    escalated: bool = Field(False, description="Si se derivó a un agente humano")
