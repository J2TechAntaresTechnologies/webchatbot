# Tutorial: Cómo funciona el bot y parametrización recomendada

Este tutorial resume el funcionamiento del bot municipal, los parámetros disponibles y configuraciones recomendadas por caso de uso.

## Arquitectura (resumen)
- API FastAPI (`services/api/main.py`): expone `/chat/message` y `/chatbots/*`.
- Orquestador (`services/orchestrator/service.py`): decide la fuente de respuesta.
- Clasificador (`services/orchestrator/intent_classifier.py`): detecta `faq`, `smalltalk`, `rag`, `handoff`, `unknown`.
- Reglas (`services/orchestrator/rule_engine.py`): respuestas instantáneas por keywords.
- RAG (`services/orchestrator/rag.py` + `knowledge/faqs/*.json`): FAQs enriquecidas por similitud.
- LLM (`services/llm_adapter/client.py`): fallback/creativo con `pre_prompts` y parámetros.

## Parámetros del bot (`chatbots/<id>/settings.json`)
- generation
  - temperature (0–2): aleatoriedad. Municipal recomendado 0.65–0.75.
  - top_p (0–1): núcleo de probabilidad. Municipal 0.85–0.9.
  - max_tokens (≥1): límite de tokens de respuesta. Municipal 180–220.
- features
  - use_rules (bool): habilita reglas FAQ/fallback.
  - use_rag (bool): habilita RAG.
  - use_generic_no_match (bool): respuesta genérica si nada coincide.
  - enable_default_rules (bool): incluye reglas por defecto del sistema.
- rag_threshold (0–1): umbral mínimo de similitud para aceptar RAG (0.25–0.35 recomendado; default 0.28).
- menu_suggestions (array): chips visibles en cliente municipal.
- pre_prompts (array): instrucciones antepuestas al LLM (estilo/seguridad).
- rules (array): reglas personalizadas (enabled, keywords[], response, source).

## Recomendaciones por variante
- Municipal (guiado)
  - use_rules=true, use_rag=true, use_generic_no_match=true, enable_default_rules=true
  - generation: temperature 0.7, top_p 0.9, max_tokens 200
  - rag_threshold: 0.28
  - pre_prompts: estilo claro, fuentes oficiales, derivar a 911/107/100 en emergencias.
  - chips: trámites online, turnos licencia, proveedores, punto violeta, consumos, discapacidad, agenda, turismo, ambiente, economía social, obras, contacto.
- MAR2 (libre)
  - use_rules=false, use_rag=false, use_generic_no_match=false
  - generation: temperature 1.0, top_p 0.98, max_tokens 256–300

## Dónde configurar
- Portal (frontend/index.html): botón “Parámetros” en cada tarjeta de bot.
- API (curl):
  - GET settings: `GET /chatbots/{id}/settings?channel=web`
  - PUT settings: `PUT /chatbots/{id}/settings`
  - POST reset: `POST /chatbots/{id}/settings/reset?channel=web`

## Buenas prácticas
- Mantener respuestas de reglas breves; enlazar a páginas oficiales.
- En RAG, redactar `question` canónica y 2–4 `tags`; mantener `answer` actualizada y concisa.
- Ajustar `rag_threshold` tras pruebas reales.
- Usar stems en `keywords` de reglas para más recall ("licenc", "conduc").
- No abusar del LLM para contenido institucional estable; preferir reglas o RAG.

