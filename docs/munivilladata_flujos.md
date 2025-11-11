# Diagramas de Flujo de Datos (Munivilla)

Este tutorial ilustra cómo fluyen los datos y decisiones desde que llega un mensaje hasta que se responde, y cómo clasificar la información para RAG/Reglas/LLM según las opciones de parametrización del bot.

## 1) Flujo de orquestación de respuestas

```
Usuario
  │
  ▼
API FastAPI: POST /chat/message (services/api/main.py)
  │  payload: {session_id, message, channel, bot_id}
  ▼
Orquestador (services/orchestrator/service.py)
  │  carga settings del bot (chatbots/<id>/settings.json)
  │  canal = "mar2" → LLM directo (salta Reglas y RAG)
  │
  │  Clasificador de intents (intent_classifier.py)
  │    ├─ faq / smalltalk → Reglas
  │    ├─ rag             → RAG
  │    └─ unknown         → Genérico (si está ON) o LLM
  │
  ├─ Reglas (rule_engine.py)
  │    ├─ match custom (settings.rules) → responder
  │    ├─ match default                 → responder
  │    └─ sin match → ¿use_generic_no_match?
  │          ├─ sí → respuesta genérica → FIN
  │          └─ no → siguiente etapa
  │
  ├─ RAG (rag.py)
  │    ├─ buscar en knowledge/faqs/*.json
  │    ├─ mejor score ≥ rag_threshold → responder → FIN
  │    └─ si no, continuar
  │
  └─ LLM (llm_adapter/client.py)
       └─ generar con pre_prompts + parámetros → FIN
```

Efecto de parámetros (settings):
- features.use_rules: habilita/inhabilita etapa de Reglas.
- features.use_rag: habilita/inhabilita etapa RAG.
- features.use_generic_no_match: activa respuesta genérica si no hay match de Reglas y el intent es unknown.
- rag_threshold: mínimo de similitud para aceptar una respuesta del RAG.
- generation.*: parámetros de temperatura/top_p/max_tokens del LLM.
- pre_prompts: políticas/estilo que se anteponen cuando se invoca LLM.

## 2) Flujo editorial de datos (curación → integración)

```
Contenido fuente (munivilladata/*.txt)
  │
  ├─ ¿Acción directa y breve (teléfono/link/turno)?
  │      └─ Sí → Regla (settings.rules[])
  │
  ├─ ¿Pregunta conceptual con contexto breve (centros, campañas, agenda)?
  │      └─ Sí → RAG (knowledge/faqs/*.json)
  │
  └─ ¿Consulta abierta/no cubierta o subjetiva?
         └─ LLM (apoyado por pre_prompts), opcionalmente crear nuevas entradas RAG en el futuro
```

## 3) Parámetros y su impacto (resumen)
- use_rules=true: aumenta precisión en lo cubierto y reduce costo LLM.
- use_rag=true: responde con datos oficiales si la similitud supera el umbral.
- use_generic_no_match=true: reduce frustración ante entradas vagas; orienta a "ayuda".
- rag_threshold: menor → más recall (pero más falsos positivos); mayor → más precisión (pero riesgo de no responder).
- temperature/top_p: controlan creatividad del LLM; valores conservadores en Municipal.

## 4) Ejemplos prácticos (casos comunes)
- “Teléfono de emergencias” → Regla fallback con números (911/107/100) y teléfono municipal.
- “Turno licencia de conducir” → Regla FAQ con enlace a turnero.
- “¿Qué es Punto Violeta?” → Entrada RAG con respuesta breve y tags.
- “¿Qué actividades hay este mes?” → RAG (Cultura/agendas) o Regla si existe un único enlace oficial a agenda.
- “Quiero emprender, ¿qué apoyo hay?” → RAG (Economía Social) o LLM si aún no hay entrada.

## 5) Checklist de integración
- [ ] Redactar preguntas/respuestas canónicas desde munivilladata/.
- [ ] Decidir Reglas vs RAG vs LLM (según criterio anterior).
- [ ] Editar `chatbots/municipal/settings.json` (rules, pre_prompts, menu_suggestions).
- [ ] Editar `knowledge/faqs/municipal_faqs.json` (entradas nuevas).
- [ ] Reiniciar API; probar consultas de regresión.

