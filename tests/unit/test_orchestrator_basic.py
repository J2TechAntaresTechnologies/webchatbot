"""Pruebas básicas del orquestador."""

import pytest

from services.orchestrator.schema import ChatRequest
from services.orchestrator.service import ChatOrchestrator


@pytest.mark.asyncio
async def test_schedule_rule() -> None:
    orchestrator = ChatOrchestrator()
    request = ChatRequest(session_id="1", message="¿Cuál es el horario de atención?", channel="web")

    response = await orchestrator.respond(request)

    assert response.source == "faq"
    assert "horarios" in response.reply.lower()


@pytest.mark.asyncio
async def test_smalltalk_rule() -> None:
    orchestrator = ChatOrchestrator()
    request = ChatRequest(session_id="smalltalk", message="hola", channel="web")

    response = await orchestrator.respond(request)

    assert response.source == "fallback"
    assert "hola" in response.reply.lower()


@pytest.mark.asyncio
async def test_help_menu() -> None:
    orchestrator = ChatOrchestrator()
    request = ChatRequest(session_id="menu", message="ayuda", channel="web")

    response = await orchestrator.respond(request)

    assert response.source == "fallback"
    assert "opciones" in response.reply.lower()
    assert "1." in response.reply


@pytest.mark.asyncio
async def test_menu_option_two() -> None:
    orchestrator = ChatOrchestrator()
    request = ChatRequest(session_id="menu2", message="opcion 2", channel="web")

    response = await orchestrator.respond(request)

    assert response.source == "faq"
    assert "chatbot" in response.reply.lower()


@pytest.mark.asyncio
async def test_fallback() -> None:
    orchestrator = ChatOrchestrator()
    request = ChatRequest(session_id="1", message="¿Cuál es la capital de Marte?", channel="web")

    response = await orchestrator.respond(request)

    assert response.source == "llm"
    assert isinstance(response.reply, str)
    assert response.reply.strip() != ""


@pytest.mark.asyncio
async def test_handoff_intent() -> None:
    orchestrator = ChatOrchestrator()
    request = ChatRequest(
        session_id="handoff",
        message="Quiero hablar con un agente humano",
        channel="web",
    )

    response = await orchestrator.respond(request)

    assert response.source == "fallback"
    assert response.escalated is True
    assert "agente" in response.reply.lower()


@pytest.mark.asyncio
async def test_rag_route() -> None:
    orchestrator = ChatOrchestrator()
    request = ChatRequest(
        session_id="rag",
        message="Necesito conocer la ordenanza vigente sobre podas",
        channel="web",
    )

    response = await orchestrator.respond(request)

    assert response.source == "rag"
    assert "ordenanza" in response.reply.lower()


# ================================================================
# Nuevas pruebas: reglas conservadoras para "cómo pagar" y "quiénes somos"
# Añadidas tras incorporar reglas en rule_engine y patrón de intent en
# intent_classifier para mejorar cobertura de FAQ sin caer al LLM.
# ================================================================


@pytest.mark.asyncio
async def test_how_to_pay_rule() -> None:
    """Verifica que "¿Cómo puedo pagar?" se resuelva por reglas (FAQ).

    Pasos:
    1) Instancia el orquestador (usa defaults con reglas activadas y RAG activado).
    2) Envía un mensaje que contiene las raíces "como" y "pag" (coinciden con la
       nueva regla conservadora y con el nuevo patrón de intent FAQ).
    3) Valida que el `source` sea "faq" (regla) y que el texto mencione pagos.
    """

    # 1) Orquestador base
    orchestrator = ChatOrchestrator()
    # 2) Mensaje del usuario (canal web municipal)
    request = ChatRequest(session_id="pay-how", message="¿Cómo puedo pagar?", channel="web")

    # 3) Respuesta
    response = await orchestrator.respond(request)

    # Debe venir de reglas (faq) y mencionar pagos
    assert response.source == "faq"
    assert "pag" in response.reply.lower()  # cubre "pagar"/"pagos"


@pytest.mark.asyncio
async def test_who_we_are_rule() -> None:
    """Verifica que "¿Quiénes son?" se responda con el texto institucional.

    Pasos:
    1) Instancia el orquestador.
    2) Envía una consulta de "quiénes" (cubierta por reglas con stems normalizados).
    3) Valida que el `source` sea "faq" y que la respuesta contenga la frase
       institucional ("Atención Digital").
    """

    orchestrator = ChatOrchestrator()
    request = ChatRequest(session_id="who", message="¿Quiénes son?", channel="web")

    response = await orchestrator.respond(request)

    assert response.source == "faq"
    assert "atención digital" in response.reply.lower()
