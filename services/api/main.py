"""Entrypoint del API Gateway basado en FastAPI."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.orchestrator.router import router as orchestrator_router
from services.chatbots.router import router as chatbots_router


def create_app() -> FastAPI:
    app = FastAPI(title="Chatbot Municipal", version="0.1.0")
    # Orígenes por defecto (desarrollo local)
    default_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://0.0.0.0:5173",
    ]
    # Permite configurar orígenes vía env para despliegues con túneles o dominios públicos.
    # Ejemplos:
    #   WEBCHATBOT_ALLOWED_ORIGINS="https://mi-dominio.com,https://api.mi-dominio.com"
    #   WEBCHATBOT_ALLOWED_ORIGINS="*"  (no recomendado en producción)
    env_origins = os.getenv("WEBCHATBOT_ALLOWED_ORIGINS", "").strip()
    if env_origins:
        if env_origins == "*":
            allowed_origins = ["*"]
        else:
            allowed_origins = [o.strip() for o in env_origins.split(",") if o.strip()]
    else:
        allowed_origins = default_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["GET", "POST", "PUT", "OPTIONS"],
        allow_headers=["*"],
    )
    app.include_router(orchestrator_router, prefix="/chat", tags=["chat"])
    app.include_router(chatbots_router, prefix="/chatbots", tags=["chatbots"])
    return app


app = create_app()

# ================================================================
# Guía rápida (API FastAPI y CORS)
# ================================================================
#
# Routers habilitados
# -------------------
# - /chat (endpoints del orquestador)
# - /chatbots (endpoints de configuración por bot)
#
# CORS
# ----
# - Por defecto permite localhost:5173 para el frontend.
# - Personalizable con la variable WEBCHATBOT_ALLOWED_ORIGINS (coma-separadas o "*").
#   Ej.: WEBCHATBOT_ALLOWED_ORIGINS="https://mi-dominio.com,https://otro.com"
#
# Ejecución local
# ---------------
# uvicorn services.api.main:app --reload
#
# Seguridad
# ---------
# - No incluye autenticación por defecto. Para exponer públicamente, configurar
#   CORS, rate limiting y auth (token/sesiones) según necesidad del entorno.
