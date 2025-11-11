"""Routers para endpoints de chat."""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Any
from pathlib import Path
import json
import re

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


# ========================
# Admin: RAG y Intents
# ========================

class RagEntry(BaseModel):
    uid: str
    question: str
    answer: str
    tags: list[str]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _faqs_path() -> Path:
    return _project_root() / "knowledge" / "faqs" / "municipal_faqs.json"


def _text_kb_dir() -> Path:
    # Usa la misma convención que el orquestador
    dflt = _project_root() / "00relevamientos_j2" / "munivilladata"
    from os import getenv
    env = getenv("WEBCHATBOT_TEXT_KB_DIR", "").strip()
    return Path(env) if env else dflt


@router.get("/admin/rag/faqs")
def admin_get_rag_faqs() -> list[dict[str, Any]]:
    p = _faqs_path()
    if not p.exists():
        return []
    # Soporta JSON con comentarios: eliminar // y /* */
    txt = p.read_text(encoding="utf-8")
    # Limpieza simple (igual a rag._strip_json_comments)
    def _strip(text: str) -> str:
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        text = re.sub(r"//.*?$", "", text, flags=re.M)
        return text
    data = json.loads(_strip(txt))
    out = []
    for it in data:
        out.append({
            "uid": it.get("uid", ""),
            "question": it.get("question", ""),
            "answer": it.get("answer", ""),
            "tags": list(it.get("tags", [])),
        })
    return out


@router.put("/admin/rag/faqs")
def admin_put_rag_faqs(payload: list[RagEntry]) -> dict:
    p = _faqs_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    data = [e.model_dump() for e in payload]
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Reindexar
    try:
        _orchestrator._bootstrap_rag()  # type: ignore[attr-defined]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error reindexando RAG: {exc}")
    return {"status": "ok", "count": len(data)}


@router.get("/admin/rag/status")
def admin_rag_status() -> dict:
    txt_dir = _text_kb_dir()
    txt_files = []
    if txt_dir.exists():
        for f in sorted(txt_dir.glob("*.txt")):
            try:
                size = f.stat().st_size
            except Exception:
                size = 0
            txt_files.append({"name": f.name, "size": size})
    count_json = len(getattr(_orchestrator, "_rag_entries", []) or [])
    return {"json_count": count_json, "txt_dir": str(txt_dir), "txt_files": txt_files}


@router.post("/admin/rag/reindex")
def admin_rag_reindex() -> dict:
    try:
        _orchestrator._bootstrap_rag()  # type: ignore[attr-defined]
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/admin/rag/texts")
def admin_list_texts() -> dict:
    d = _text_kb_dir()
    d.mkdir(parents=True, exist_ok=True)
    files = []
    for f in sorted(d.glob("*.txt")):
        files.append({"name": f.name, "size": f.stat().st_size})
    return {"dir": str(d), "files": files}


@router.put("/admin/rag/texts/{name}")
def admin_put_text(name: str, content: str = Body(..., media_type="text/plain")) -> dict:
    if not re.match(r"^[A-Za-z0-9._-]+$", name):
        raise HTTPException(status_code=400, detail="Nombre inválido")
    d = _text_kb_dir()
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(content, encoding="utf-8")
    return {"status": "ok", "name": name, "size": len(content.encode('utf-8'))}


@router.delete("/admin/rag/texts/{name}")
def admin_delete_text(name: str) -> dict:
    if not re.match(r"^[A-Za-z0-9._-]+$", name):
        raise HTTPException(status_code=400, detail="Nombre inválido")
    p = _text_kb_dir() / name
    if p.exists():
        p.unlink()
    return {"status": "ok"}


class IntentPatternDTO(BaseModel):
    intent: str
    keywords: list[str]
    confidence: float | None = None


def _intents_path() -> Path:
    return _project_root() / "config" / "intents.json"


@router.get("/admin/intents")
def admin_get_intents() -> dict:
    p = _intents_path()
    if not p.exists():
        # Devolver patrones actuales del clasificador
        pats = [
            {"intent": it.intent, "keywords": list(it.keywords), "confidence": it.confidence}
            for it in _orchestrator._classifier.patterns  # type: ignore[attr-defined]
        ]
        return {"patterns": pats, "source": "memory"}
    data = json.loads(p.read_text(encoding="utf-8"))
    return {"patterns": data.get("patterns", []), "source": str(p)}


@router.put("/admin/intents")
def admin_put_intents(payload: dict) -> dict:
    pats_in = payload.get("patterns", [])
    try:
        pats = [IntentPatternDTO.model_validate(p).model_dump() for p in pats_in]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Patrones inválidos: {exc}")
    p = _intents_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"patterns": pats}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Reconfigurar clasificador
    from services.orchestrator.intent_classifier import IntentPattern, IntentClassifier
    seq = [IntentPattern(intent=x["intent"], keywords=tuple(x["keywords"]), confidence=float(x.get("confidence") or 0.6)) for x in pats]
    _orchestrator._classifier = IntentClassifier(patterns=tuple(seq))  # type: ignore[attr-defined]
    return {"status": "ok", "count": len(pats)}
