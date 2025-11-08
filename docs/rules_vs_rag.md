# Motor de Reglas (FAQ) vs RAG — Guía práctica del proyecto

Este documento explica la diferencia entre el motor de Reglas (Rule Engine) y el RAG en este repositorio, cómo decide el orquestador a cuál llamar, y qué cambios recientes aplicamos para mejorar coberturas como “cómo pagar” y “quiénes somos”.

## Qué es cada componente

- Rule Engine (FAQ)
  - Responde con textos fijos cuando el mensaje coincide por palabras clave (match AND) tras normalizar (minúsculas, sin tildes).
  - Implementación: `services/orchestrator/rule_engine.py` (clase `Rule` y colección `DEFAULT_RULES`).
  - Origen de respuesta: suele salir con `source="faq"` (o `fallback` para smalltalk puntuales).
  - Ventajas: latencia mínima, 100% determinista, ideal para “cómo pagar”, “horario”, “contacto”, “quiénes somos”, “ayuda/menú”.
  - Mantenimiento: se curan keywords (stems) y textos.

- RAG (Recuperación en base de conocimiento)
  - Busca en un dataset de FAQs (`knowledge/faqs/municipal_faqs.json`) por similitud léxica y devuelve la mejor respuesta si supera el umbral.
  - Implementación: `services/orchestrator/rag.py` (`SimpleRagResponder`), tokenización + TF simple y similitud coseno.
  - Origen de respuesta: `source="rag"`.
  - Ventajas: más flexible ante variaciones de redacción sin definir todas las reglas; útil para normativa, trámites varios, etc.

## Cómo decide el orquestador

Ruta de decisión en `services/orchestrator/service.py`:
1. Si el canal es libre (`mar2`/`free`) → LLM directo con `pre_prompts` si existen.
2. Si el intent es `handoff` → devuelve derivación (`source=fallback`, `escalated=true`).
3. Si `intent ∈ {faq, smalltalk}` y `use_rules=true` → intenta Reglas; si matchea, responde y termina.
4. Si no respondió y `intent == rag` y `use_rag=true` → intenta RAG; si supera umbral, responde y termina.
5. Si nada aplica → LLM con `pre_prompts` si están configurados.

El intent lo fija el clasificador heurístico (`services/orchestrator/intent_classifier.py`) por match AND de keywords normalizadas, evaluando patrones en orden.

## Cambios recientes aplicados (mejoras de cobertura)

Para cubrir consultas reales como “¿Cómo puedo pagar?” y “¿Quiénes son?”, aplicamos estos cambios:

- Reglas nuevas en `services/orchestrator/rule_engine.py` (colección `DEFAULT_RULES`):
  - Pagos genérico: `keywords=("como", "pag")` → respuesta oficial de pagos (igual a la regla de “pag/impuest”).
  - Quiénes somos: `keywords=("quien","somos")` y `keywords=("quien","son")` → texto institucional (“Somos el equipo de Atención Digital…”).

- Patrones de intent en `services/orchestrator/intent_classifier.py` (colección `DEFAULT_PATTERNS`):
  - FAQ: `("como", "pag")`, `("quien","somos")` y `("quien","son")`.
  - Motivo: habilitar que esas consultas entren al motor de Reglas (paso 3 del orquestador) en lugar de caer al LLM.

- Ajustes de configuración en `chatbots/municipal/settings.json`:
  - `generation.max_tokens`: 220 (evita truncados cuando se usa LLM).
  - `pre_prompts`: sustituidos por indicaciones concisas para evitar formato “faq/rag” y alucinaciones de estructura:
    - “Responde en 1–2 oraciones, sin viñetas ni listados.”
    - “Usa solo información municipal oficial; si no sabés, ofrecé 'ayuda'.”
    - “No uses formato 'faq' ni 'rag' en tus respuestas.”
  - `features.use_generic_no_match` + `no_match_replies`: si está activado, el orquestador responde con un texto genérico cuando:
    - (a) el intent es `faq`/`smalltalk` y no hubo match de reglas, o
    - (b) el intent es `unknown`.

- Pruebas unitarias nuevas en `tests/unit/test_orchestrator_basic.py`:
  - `test_how_to_pay_rule`: valida que “¿Cómo puedo pagar?” responda por regla (source=`faq`).
  - `test_who_we_are_rule`: valida que “¿Quiénes son?” responda con el texto institucional (source=`faq`).

## Cuándo usar cada camino

- Usar Reglas cuando la respuesta es oficial, frecuente y no debe variar: “cómo pagar”, “quiénes somos”, “horarios”, “contacto”, “ayuda/menú”.
- Usar RAG para amplitud semántica sobre un corpus curado de FAQs/ordenanzas: “ordenanza de podas”, “habilitaciones”, “expedientes”.

## Cómo ampliar (paso a paso)

- Agregar una regla
  1) Editar `services/orchestrator/rule_engine.py` y añadir una `Rule(keywords=..., response=..., source=...)`.
  2) Preferir stems (raíces) como “pag”, “impuest”, “quien”, “somos”. Evitar tokens demasiado genéricos.
  3) Orden importa: la primera coincidencia gana.

- Agregar contenido a RAG
  1) Editar `knowledge/faqs/municipal_faqs.json` (admite comentarios JSONC). Cada entrada: `uid`, `question`, `answer`, `tags`.
  2) Reiniciar el backend para reindexar en memoria.
  3) Ajustar `threshold` de `SimpleRagResponder` si hiciera falta (default 0.28).

- Ajustar intent
  1) Editar `services/orchestrator/intent_classifier.py` para añadir `IntentPattern(intent="faq"|"rag", keywords=(...), confidence=...)`.
  2) Colocar primero patrones más específicos.

### Manipular patrones RAG (intents)

Los "tags" del dataset RAG mejoran la recuperación, pero RAG solo corre si el intent es `rag`. Para canalizar consultas hacia RAG, añadí patrones `IntentPattern(intent="rag", ...)` en `DEFAULT_PATTERNS`:

```python
# services/orchestrator/intent_classifier.py
DEFAULT_PATTERNS: Sequence[IntentPattern] = (
    # ...
    IntentPattern(intent="rag", keywords=("ordenanza",), confidence=0.6),
    IntentPattern(intent="rag", keywords=("normativa",), confidence=0.6),
    # Stems para permisos de poda/ambiente → activa RAG con consultas del tipo
    # "ambiente permisos podas" o "poda".
    IntentPattern(intent="rag", keywords=("ambiente", "permis"), confidence=0.65),
    IntentPattern(intent="rag", keywords=("poda",), confidence=0.65),
)
```

Recomendaciones:
- Usar stems normalizados (el clasificador compara contra minúsculas sin tildes).
- Orden importa: el primero que matchea gana. Colocá antes los más específicos.
- Evitá patrones demasiado amplios (ej. solo `"tramite"`) salvo que realmente quieras abrir RAG a muchas consultas.

Verificación:
- Con el cambio anterior, mensajes como "ambiente permisos podas" clasifican `rag`.
- RAG tokeniza el mensaje y compara contra `question + tags` (por eso `tags`=["ambiente","permisos","podas"] ayuda).


## Validación

- Ejecutar tests: `python3 -m pytest -q`
  - Cobertura clave en `tests/unit/test_orchestrator_basic.py`: rutas de Regla, RAG, LLM, Handoff, y las nuevas pruebas de pagos/quiénes.

## Referencias rápidas (archivos)

- Rule Engine: `services/orchestrator/rule_engine.py`
- RAG ligero: `services/orchestrator/rag.py`
- Clasificador de intents: `services/orchestrator/intent_classifier.py`
- Orquestador (flujo): `services/orchestrator/service.py`
- Settings por bot: `chatbots/municipal/settings.json`
- Dataset RAG: `knowledge/faqs/municipal_faqs.json`
- Pruebas: `tests/unit/test_orchestrator_basic.py`
