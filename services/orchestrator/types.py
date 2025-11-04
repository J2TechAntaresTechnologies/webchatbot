"""Tipos compartidos del orquestador."""

from dataclasses import dataclass
from typing import Literal, Protocol

ResponseSource = Literal["faq", "rag", "llm", "fallback"]
IntentName = Literal["faq", "rag", "handoff", "smalltalk", "unknown"]


@dataclass(frozen=True)
class IntentPrediction:
    """Resultado de clasificación de intents."""

    intent: IntentName
    confidence: float


class RagResponderProtocol(Protocol):
    """Contrato mínimo para conectores RAG."""

    async def search(self, message: str) -> str | None:  # pragma: no cover - contrato
        """Busca una respuesta en la base de conocimiento. Devuelve None si no hay match."""
