"""Implementación ligera de RAG basada en similitud léxica."""

from __future__ import annotations

import json
from dataclasses import dataclass
from math import sqrt
from pathlib import Path
from typing import Iterable, Sequence

from services.orchestrator.text_utils import normalize_text


@dataclass(frozen=True)
class KnowledgeEntry:
    """Entrada simple de la base de conocimiento."""

    uid: str
    question: str
    answer: str
    tags: Sequence[str]


class SimpleRagResponder:
    """Busca respuestas en una base de conocimiento embebida en memoria."""

    def __init__(self, entries: Sequence[KnowledgeEntry], threshold: float = 0.28) -> None:
        self._entries = entries
        self._threshold = threshold
        self._vectors = [self._embed(entry) for entry in entries]

    async def search(self, message: str) -> str | None:
        query_vector = self._embed_text(message)
        if not query_vector:
            return None

        best_score = 0.0
        best_answer: str | None = None
        for entry, vector in zip(self._entries, self._vectors):
            score = _cosine_similarity(query_vector, vector)
            if score > best_score:
                best_score = score
                best_answer = entry.answer

        if best_answer is None or best_score < self._threshold:
            return None
        return best_answer

    def _embed(self, entry: KnowledgeEntry) -> dict[str, float]:
        text = " ".join([entry.question, *entry.tags])
        return self._embed_text(text)

    @staticmethod
    def _embed_text(text: str) -> dict[str, float]:
        tokens = _tokenize(text)
        if not tokens:
            return {}
        total = float(len(tokens))
        vector: dict[str, float] = {}
        for token in tokens:
            vector[token] = vector.get(token, 0.0) + 1.0 / total
        return vector


def load_default_entries(path: Path | None = None) -> Sequence[KnowledgeEntry]:
    """Carga entradas de la carpeta `knowledge/faqs`."""

    base_path = path or Path(__file__).resolve().parents[2] / "knowledge" / "faqs" / "municipal_faqs.json"
    with base_path.open("r", encoding="utf-8") as fh:
        payload: Iterable[dict[str, object]] = json.load(fh)
    entries: list[KnowledgeEntry] = []
    for item in payload:
        entries.append(
            KnowledgeEntry(
                uid=str(item.get("uid")),
                question=str(item.get("question")),
                answer=str(item.get("answer")),
                tags=tuple(str(tag) for tag in item.get("tags", [])),
            )
        )
    return entries


def _tokenize(text: str) -> list[str]:
    normalized = normalize_text(text)
    tokens = [token for token in normalized.split() if token]
    return tokens


def _cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    if not vec_a or not vec_b:
        return 0.0

    common = set(vec_a).intersection(vec_b)
    numerator = sum(vec_a[token] * vec_b[token] for token in common)
    if numerator == 0:
        return 0.0

    norm_a = sqrt(sum(value * value for value in vec_a.values()))
    norm_b = sqrt(sum(value * value for value in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0

    return numerator / (norm_a * norm_b)

# ================================================================
# Guía de uso, parametrización e impacto (RAG ligero)
# ================================================================
#
# ¿Qué hace?
# -----------
# Carga entradas de conocimiento (pregunta, respuesta, tags) desde JSON y
# aplica una similitud léxica simple (bag-of-words normalizada) para recuperar
# una respuesta si supera un umbral.
#
# Uso básico
# -----------
# from services.orchestrator.rag import load_default_entries, SimpleRagResponder
# entries = load_default_entries()  # knowledge/faqs/municipal_faqs.json
# rag = SimpleRagResponder(entries, threshold=0.28)
# reply = await rag.search("¿Dónde consulto la ordenanza de poda?")
# if reply is not None: ...
#
# Parametrización
# ---------------
# - threshold: elevarlo reduce falsos positivos (más precision, menos recall).
# - dataset: modificar/expandir knowledge/faqs/*.json con campos uid,question,answer,tags.
# - tokenización: se usa normalize_text() y conteo proporcional; términos en tags ayudan a recall.
#
# Impacto en el bot
# -----------------
# - Con use_rag=True, el orquestador consultará RAG cuando el intent sea "rag".
# - Buen dataset + tags relevantes mejoran precisión y reducen caídas al LLM.
#
# Escalamiento
# ------------
# - Para pasar a embeddings reales y vector store (Chroma/Qdrant), implementar un
#   conector que cumpla RagResponderProtocol (método async search) y usar attach_rag().
