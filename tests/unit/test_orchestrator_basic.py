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
