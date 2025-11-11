# Base de Conocimiento (KB) del Chatbot Municipal

Este documento explica qué es la base de conocimiento del proyecto, cómo se aplica en tiempo de ejecución, cómo está estructurada, qué parámetros la gobiernan y cómo ampliarla. Incluye diagramas de flujo ASCII para entender el recorrido de los datos y las decisiones.

## Qué es la KB y dónde vive
- Archivo principal: `knowledge/faqs/municipal_faqs.json:1`.
- Formato: JSON con soporte de comentarios (JSONC). Se permiten `// ...` y bloques `/* ... */` dentro del archivo.
- Contenido: entradas de tipo pregunta-respuesta con etiquetas para mejorar la recuperación.
- Carga: `services/orchestrator/rag.py:1` lee y limpia comentarios (`_strip_json_comments`), crea instancias `KnowledgeEntry` y vectoriza en memoria.

## Estructura de las entradas
Cada ítem de la KB tiene el siguiente esquema:
- `uid` (string): identificador único y estable para trazabilidad.
- `question` (string): pregunta canónica y breve, en lenguaje ciudadano.
- `answer` (string): respuesta oficial y concisa (recomendado < 800 caracteres). Puede incluir enlaces o áreas responsables.
- `tags` (array<string>): 2–4 etiquetas en minúscula y sin tildes para reforzar la señal semántica (ej.: `"dengue"`, `"violeta"`).

Ejemplo (JSONC):
```jsonc
{
  "uid": "vc-001",
  "question": "¿Qué es y dónde está el Punto Violeta?",
  "answer": "Punto Violeta brinda escucha y contención en temas de género. Consultá ubicación/horarios en genero.municipio.gob.",
  "tags": ["genero", "violeta", "igualdad", "apoyo"]
}
```

## Cómo se aplica en tiempo de ejecución
- El orquestador (`services/orchestrator/service.py:1`) consulta la KB mediante el componente RAG (`services/orchestrator/rag.py:1`).
- La recuperación usa similitud léxica simple (bag-of-words + coseno) entre la consulta y `question+tags` de cada entrada.
- Si la mejor similitud es ≥ `rag_threshold` (por bot), se devuelve `answer`. Si no, el flujo continúa (genérico/LLM).

Parámetros que afectan la KB
- `features.use_rag` (bool): habilita/deshabilita la fase RAG.
- `rag_threshold` (0–1): umbral mínimo de similitud para aceptar una respuesta (recomendado 0.25–0.35, default 0.28).
- Ubicación: `chatbots/<id>/settings.json:1` (por ejemplo, `chatbots/municipal/settings.json:1`).

Clasificación previa (intents)
- El clasificador (`services/orchestrator/intent_classifier.py:1`) decide si una consulta debe tratarse como `rag` (además de `faq`, `smalltalk`, `handoff`, `unknown`).
- Patrones típicos para KB Munivilla: `("licenc","conduc")`, `("proveedor","inscrip")`, `("discap","certific")`, `("genero","violeta")`, `("dengue")`.

## Flujo de decisión (canal Municipal / web)
```
Usuario
  │  (POST /chat/message)
  ▼
Clasificador de intents
  ├─ faq/smalltalk → Reglas (respuestas rápidas)
  │     ├─ match custom (settings.rules) → RESPUESTA
  │     ├─ match default                → RESPUESTA
  │     └─ sin match → sigue
  ├─ rag → RAG (KB municipal)
  │     ├─ score ≥ rag_threshold → RESPUESTA
  │     └─ score < rag_threshold → sigue
  ├─ handoff → RESPUESTA de derivación a humano
  └─ unknown →
        ├─ use_generic_no_match = true → RESPUESTA genérica (sugerir "ayuda")
        └─ else → LLM
  
Si nada responde antes → LLM (con pre_prompts y parámetros)
```

Flujo en canal libre (MAR2)
```
Usuario (channel = mar2)
  └─→ LLM directo (se salta Reglas y RAG) con pre_prompts y parámetros del bot
```

Proceso editorial / de curación (de textos a KB/Reglas)
```
Texto fuente (munivilladata)  
  ├─ ¿Respuesta corta y de acción (teléfono/link/turno)?
  │      └─ Regla en settings.rules (FAQ/fallback)
  ├─ ¿Pregunta con contexto breve y estable (servicio/programa/campaña)?
  │      └─ Entrada KB en knowledge/faqs/municipal_faqs.json
  └─ ¿Consulta abierta/no cubierta?
         └─ LLM (considerar crear entradas RAG si se repite)
```

## Interacción con Reglas y LLM
- Prioridad: Reglas → RAG → Genérico (opcional) → LLM.
- Reglas (`settings.rules[]`) responden al instante si hacen match de keywords (stems). Son ideales para: emergencias, turnos, proveedores, accesos a portales.
- RAG brinda respuestas breves, estructuradas y trazables; ideal para campañas, centros, programas y trámites comunes.
- LLM completa donde no hay cobertura de reglas/KB, con estilo condicionado por `pre_prompts`.

## Rendimiento y límites
- La KB se vectoriza en memoria al iniciar la API (`_bootstrap_rag`). Cambios en el archivo requieren reiniciar la API para reindexar.
- Escala: adecuado para cientos o pocos miles de entradas. Para mayor tamaño o semántica más rica, migrar a embeddings densos / vector store.

## Buenas prácticas editoriales
- Usar etiquetas consistentes (minúsculas, sin tildes).
- Mantener `question` concreta y `answer` concisa, con enlaces y áreas responsables.
- No duplicar `uid`. Actualizar `answer` ante cambios normativos o de proceso.
- Validar tras cambios con un set de consultas de regresión.

## Cómo ampliar la KB (paso a paso)
1) Redactar nuevas entradas (uid, question, answer, tags) y agregarlas a `knowledge/faqs/municipal_faqs.json` (JSONC válido).
2) Reiniciar `uvicorn` para reindexar el dataset.
3) Probar consultas; ajustar `rag_threshold` según recall/precisión.
4) (Opcional) Añadir patrones `rag` en el clasificador si la intención es específica y recurrente.

## Dónde tocar (referencias de archivos)
- KB: `knowledge/faqs/municipal_faqs.json:1`
- RAG: `services/orchestrator/rag.py:1`
- Orquestador: `services/orchestrator/service.py:1`
- Clasificador: `services/orchestrator/intent_classifier.py:1`
- Reglas y parámetros por bot: `chatbots/municipal/settings.json:1`
