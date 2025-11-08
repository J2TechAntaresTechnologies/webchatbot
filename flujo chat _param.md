# Flujo del Chat Municipal y Parámetros de Configuración

Este documento describe en detalle cómo decide respuestas el chatbot municipal, qué parámetros lo controlan y múltiples ejemplos que muestran el impacto de combinaciones de features, pre-prompts y reglas (FAQ/fallback).

Referencias de código:
- Orquestador: `services/orchestrator/service.py`
- Motor de reglas: `services/orchestrator/rule_engine.py`
- RAG básico: `services/orchestrator/rag.py`
- Esquema de settings por bot: `services/chatbots/models.py`
- Settings actuales municipal: `chatbots/municipal/settings.json`

---

## Parámetros relevantes (settings por bot)

- `features.use_rules` (bool): activa el motor de reglas/FAQ.
- `features.use_rag` (bool): activa recuperación RAG antes de llamar al LLM.
- `features.use_generic_no_match` (bool): si no hay match y el intent es "unknown", responde con un genérico tomado de `no_match_replies` (evita ir al LLM para consultas vagas).
- `features.enable_default_rules` (bool): incluye las reglas por defecto además de las personalizadas (`rules`).
- `rules` (lista): reglas personalizadas. Cada una con: `enabled`, `keywords` (stems), `response`, `source` ("faq" | "fallback").
- `pre_prompts` (lista de strings): instrucciones que se inyectan antes del prompt del usuario cuando se llama al LLM.
- `no_match_replies` (lista de strings) + `no_match_pick` ("first" | "random"): plantillas para el genérico.
- `rag_threshold` (float 0–1): umbral mínimo de similitud para que RAG devuelva respuesta.
- `generation.temperature/top_p/max_tokens`: hiperparámetros que se pasan al LLM (afectan estilo y longitud, no el flujo).
- `menu_suggestions` (lista): afecta sólo al frontend (chips), no al enrutamiento de backend.
- `channel` (string, por request): si es `mar2` o `free`, se forza conversación libre → LLM directo (ignora reglas y RAG).

---

## Diagrama de flujo (lógica de decisión)

```mermaid
flowchart TD
    A[Inicio: llega POST /chat/message] --> B{Canal es mar2/free?}
    B -- Sí --> B1[Compose pre_prompts + mensaje]
    B1 --> B2[LLM.generate]
    B2 --> Z[Respuesta {source: "llm"}]

    B -- No --> C[Intents: IntentClassifier]
    C -->|handoff| C1[Derivar: texto de derivación]
    C1 --> ZH[Respuesta {source: "fallback", escalated: true}]

    C -->|faq/smalltalk| D{features.use_rules?}
    D -- No --> E
    D -- Sí --> D1[Intentar reglas (custom + default si enable_default_rules)]
    D1 -->|match| ZR[Respuesta de la regla {source: "faq"/"fallback"}]
    D1 -->|no match| D2{features.use_generic_no_match?}
    D2 -- Sí --> D3[Elegir texto en no_match_replies]
    D3 --> ZG1[Respuesta {source: "fallback"}]
    D2 -- No --> E[Continuar]

    C -->|rag/unknown/otros| E

    E{features.use_rag?} -- No --> F
    E -- Sí --> E1[Buscar en RAG con rag_threshold]
    E1 -->|>= threshold| ZRAG[Respuesta RAG {source: "rag"}]
    E1 -->|< threshold| F

    F{intent == unknown AND use_generic_no_match?}
    F -- Sí --> F1[Elegir genérico en no_match_replies]
    F1 --> ZG2[Respuesta {source: "fallback"}]
    F -- No --> G[Compose pre_prompts + mensaje]
    G --> H[LLM.generate]
    H --> Z
```

Notas clave del flujo:
- Reglas sólo se intentan si el intent clasificado es `faq` o `smalltalk` y `use_rules=true`.
- RAG se intenta si `use_rag=true`, y devuelve respuesta sólo si supera `rag_threshold`.
- El genérico por `use_generic_no_match` puede activarse justo tras fallar reglas (para faq/smalltalk) o al final si el intent fue `unknown`.
- En canal `mar2/free` no se ejecuta nada de reglas/RAG: es LLM directo (pero sí aplica `pre_prompts`).

---

## Escenarios representativos por combinaciones de features

1) Reglas + RAG activados (municipal por defecto)
- `use_rules=true`, `enable_default_rules=true`, `use_rag=true`, `use_generic_no_match=true`, `rag_threshold=0.28`.
- Consulta: "¿Horario de atención?" → coincide con regla default → Respuesta `source="faq"`.
- Consulta: "Ordenanza de podas vigente" → si similitud RAG ≥ 0.28 → `source="rag"`; si no, cae al comportamiento genérico/LLM según intent.

2) Sólo Reglas (RAG off)
- `use_rules=true`, `use_rag=false`.
- Consulta: "Pagar impuestos" con regla custom → `source="faq"`.
- Consulta: "Cuál es la capital de Marte" → sin match; si `use_generic_no_match=true` → genérico `source="fallback"`; si `false` → LLM.

3) Sólo RAG (Reglas off)
- `use_rules=false`, `use_rag=true`.
- Consulta: "podas" → RAG intenta; si score < umbral → LLM (con `pre_prompts`).

4) Sin Reglas ni RAG (LLM puro)
- `use_rules=false`, `use_rag=false`.
- Toda consulta cae en LLM; estilo afectado por `pre_prompts` y `generation`.

5) Canal libre `mar2`/`free`
- Independiente de toggles: siempre LLM directo con `pre_prompts`.

6) Genérico temprano tras reglas
- Intent `faq/smalltalk`, `use_rules=true`, no hay match, `use_generic_no_match=true` → devuelve genérico sin ir a RAG/LLM.

7) Genérico tardío por intent `unknown`
- Intent `unknown`, `use_generic_no_match=true` → devuelve genérico al final si RAG no aplicó.

---

## Ejemplos de impacto de pre-prompts

Supongamos `pre_prompts`:
- "Usá un tono formal y respetuoso."
- "Responde en no más de 2 oraciones."

Consulta: "Quiero sacar un turno"
- Sin pre-prompts: "Ingresá en turnos.municipio.gob para solicitar o reprogramar tu turno municipal."
- Con pre-prompts: "Por favor, accedé a turnos.municipio.gob para solicitar o reprogramar tu turno. Gracias."

Otro set de `pre_prompts`:
- "Incluí siempre una advertencia sobre horarios si corresponde."
- "Evitá tecnicismos; lenguaje sencillo."

Consulta: "¿Hasta qué hora atienden?"
- Respuesta LLM: "Atendemos de lunes a viernes de 9 a 17 hs. Recordá que los sábados sólo operan trámites rápidos de 9 a 13 hs."

Observaciones:
- `pre_prompts` sólo impactan cuando el flujo llega al LLM (canal libre, o tras no aplicar reglas/RAG, o por diseño de `unknown` sin genérico).
- Se concatenan antes del mensaje en la forma de una lista de instrucciones, lo que guía estilo, formato y límites de longitud.

---

## Ejemplos de reglas (FAQ vs Fallback)

Reglas default (ejemplos reales del código):
- FAQ: keywords ("horario", "atencion") → respuesta con horarios → `source="faq"`.
- FAQ: keywords ("pag", "impuest") → respuesta sobre pagos → `source="faq"`.
- Fallback: keywords ("hola") → saludo → `source="fallback"`.
- Fallback: keywords ("ayuda") → menú numerado → `source="fallback"`.

Regla personalizada (desde settings), ya presente en `chatbots/municipal/settings.json`:
```json
{
  "enabled": true,
  "keywords": ["impuestos"],
  "response": "Podes pagar impuestos en www.impuestosvilla.com",
  "source": "faq"
}
```

Comportamientos esperados:
- Mensaje: "Necesito pagar mis impuestos" → match con regla custom → `source="faq"`, respuesta personalizada.
- Mensaje: "hola" → match con default → `source="fallback"`.
- Mensaje: "ayuda" → menú numerado (default) → `source="fallback"`.
- Mensaje: "Cómo puedo pagar?" → puede matchear default (stems "como" + "pag") → `source="faq"`.

Notas sobre matching:
- El motor normaliza texto (minúsculas, sin tildes) y hace coincidencia por subcadenas de los `keywords` (stems), con lógica AND por defecto.
- Las reglas personalizadas aceptan `source` "faq" o "fallback" para trazabilidad; no exponen `min_matches` por settings.
- Si `enable_default_rules=false`, sólo corren las reglas personalizadas.

---

## Efecto de `use_generic_no_match` y `no_match_replies`

Settings de ejemplo:
```json
{
  "features": { "use_generic_no_match": true },
  "no_match_replies": [
    "No tengo una respuesta exacta para eso. Podés escribir 'ayuda' para ver el menú o reformular en pocas palabras.",
    "No estoy entendiendo. Si escribís 'ayuda', puedo mostrarte opciones."
  ],
  "no_match_pick": "random"
}
```

- Caso A (tras fallar reglas en intent faq/smalltalk): devuelve de inmediato una de las plantillas anteriores, `source="fallback"`.
- Caso B (intent `unknown` al final del flujo): si RAG no respondió y sigue `unknown`, aplica el mismo mecanismo.

---

## Efecto de `rag_threshold`

- Umbral bajo (p.ej., 0.20): mayor recall, riesgo de falsos positivos.
- Umbral alto (p.ej., 0.40): mayor precisión, pero más "no encontró" → cae a genérico/LLM.

Ejemplo:
- Consulta: "¿Cuál es la ordenanza sobre podas?"
- Con `rag_threshold=0.28` y dataset adecuado: `source="rag"` con respuesta normativa.
- Con `rag_threshold=0.45`: misma consulta podría no alcanzar el umbral y terminar en LLM o genérico según intent/toggles.

---

## Matriz de escenarios con ejemplos

A) Reglas primero, genérico temprano
- `use_rules=true`, `enable_default_rules=true`, `use_generic_no_match=true`, `use_rag=false`.
- Entrada: "Necesito tramitar certificado de domicilio" (sin regla específica)
- Salida: genérico de `no_match_replies` (`source="fallback"`).

B) Reglas + RAG, sin genérico
- `use_rules=true`, `use_rag=true`, `use_generic_no_match=false`.
- Entrada: "Ordenanzas sobre residuos" (sin regla, con conocimiento en RAG)
- Salida: RAG (`source="rag"`). Si RAG < threshold → LLM.

C) RAG sólo
- `use_rules=false`, `use_rag=true`.
- Entrada: "podas árboles" → RAG o LLM según umbral.

D) LLM con estilo guiado por pre-prompts
- `use_rules=false`, `use_rag=false`, `pre_prompts=["Respondé con bullet points", "Texto breve"]`.
- Entrada: "Requisitos para habilitación comercial"
- Salida: LLM con lista breve (si el modelo lo respeta) (`source="llm"`).

E) Canal libre mar2/free
- `channel="mar2"` o `"free"`.
- Entrada: cualquiera.
- Salida: LLM directo con `pre_prompts` (`source="llm"`).

---

## Buenas prácticas para ajustar parámetros

- Empezá con `use_rules=true`, `enable_default_rules=true` y añadí reglas personalizadas para preguntas frecuentes locales.
- Activá `use_rag=true` cuando tengas una base de conocimiento curada; ajustá `rag_threshold` con pruebas reales.
- Usá `use_generic_no_match=true` si querés evitar respuestas de LLM en consultas vagas.
- Redactá `pre_prompts` concisos y específicos; evitá contradicciones entre instrucciones.
- Documentá cada regla personalizada y revisá que los `keywords` sean stems (subcadenas) que capturen variaciones.

---

## Resumen

- El flujo prioriza: Reglas/FAQ → RAG → LLM, con cortocircuitos por `handoff` y genéricos configurables.
- `channel=mar2/free` salta todo: LLM directo.
- Los parámetros en `chatbots/<id>/settings.json` permiten modular precisión, costos y estilo.

