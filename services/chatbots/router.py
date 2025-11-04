"""Router para configuración de chatbots (persistente en servidor)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from services.chatbots.models import (
    BotSettings,
    load_settings,
    reset_settings,
    save_settings,
)


router = APIRouter()


@router.get("/{bot_id}/settings", response_model=BotSettings)
def get_settings(bot_id: str, channel: str | None = None) -> BotSettings:
    return load_settings(bot_id, channel=channel)


@router.put("/{bot_id}/settings", response_model=BotSettings)
def put_settings(bot_id: str, payload: BotSettings) -> BotSettings:
    try:
        save_settings(bot_id, payload)
    except Exception as exc:  # pragma: no cover - errores de IO
        raise HTTPException(status_code=500, detail=str(exc))
    return load_settings(bot_id)


@router.post("/{bot_id}/settings/reset", response_model=BotSettings)
def post_reset(bot_id: str, channel: str | None = None) -> BotSettings:
    try:
        return reset_settings(bot_id, channel=channel)
    except Exception as exc:  # pragma: no cover - errores de IO
        raise HTTPException(status_code=500, detail=str(exc))


# ================================================================
# Guía de uso (API de settings por bot)
# ================================================================
#
# Endpoints y ejemplos (curl)
# ---------------------------
# - GET /chatbots/{id}/settings?channel=web
#   curl -sS "http://127.0.0.1:8000/chatbots/municipal/settings?channel=web" | jq .
#
# - PUT /chatbots/{id}/settings
#   curl -sS -X PUT "http://127.0.0.1:8000/chatbots/municipal/settings" \
#     -H 'Content-Type: application/json' -d '{"generation":{"temperature":0.7,"top_p":0.9,"max_tokens":256},"features":{"use_rules":true,"use_rag":true}}' | jq .
#
# - POST /chatbots/{id}/settings/reset?channel=web
#   curl -sS -X POST "http://127.0.0.1:8000/chatbots/municipal/settings/reset?channel=web" | jq .
#
# Consideraciones
# ---------------
# - Persistencia en disco: chatbots/<id>/settings.json (crea carpeta si falta).
# - Validación Pydantic: estructura y límites por modelo (ver services.chatbots.models).
# - Errores de IO → 500 con detalle del error.
# - Seguridad/CORS: depende de configuración en services.api.main (variable WEBCHATBOT_ALLOWED_ORIGINS).
