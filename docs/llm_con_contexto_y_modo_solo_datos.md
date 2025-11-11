# LLM con Contexto (Grounded) y Modo “Solo Datos”

Este documento explica las nuevas funcionalidades para generar respuestas usando exclusivamente el conocimiento cargado (KB), evitando alucinaciones, y cómo activarlas desde el Portal o por API. Incluye paso a paso para agregar casos en Reglas, RAG (JSON) y RAG (TXT), con ejemplos.

## 1) Objetivo
- Generar respuestas ancladas a datos municipales (FAQs + textos curatoriales), reduciendo invenciones del LLM.
- Controlar el “fallback” del orquestador: si no hay match de Reglas ni RAG, el LLM ahora se alimenta de trozos relevantes (top‑k) de la KB.
- Opcional: Modo “Solo datos”, que se abstiene de invocar LLM cuando no hay contexto suficiente.

## 2) Componentes involucrados
- RAG ligero: `services/orchestrator/rag.py`
  - FAQs JSON (con comentarios): `knowledge/faqs/municipal_faqs.json`.
  - Textos curatoriales: `.txt` en `00relevamientos_j2/munivilladata/` (indexación automática al iniciar).
  - Búsqueda top‑k (nuevo): `SimpleRagResponder.topk()`.
- Orquestador: `services/orchestrator/service.py`
  - Fallback con contexto: arma un prompt con pasajes relevantes + instrucciones “usar solo contexto”.
  - `grounded_only` (settings/env): si está activo y no hay contexto, se abstiene.
- Portal (frontend): `frontend/index.html` + `frontend/portal.js`
  - Nuevo toggle: “Solo datos (sin LLM si no hay match)”.
  - Editor de reglas con “Min matches”.
  - Lista blanca de dominios (allowed_domains) para enlaces en respuestas.

## 3) Activación y defaults
- Por defecto en Municipal:
  - `use_rules=true`, `use_rag=true`, `grounded_only=true`, `use_generic_no_match=false`.
  - `rag_threshold=0.28`.
  - `allowed_domains`: `municipio.gob`, `municipio.gob.ar`, `tramites.municipio.gob`, `proveedores.municipio.gob`, `salud.municipio.gob`, `genero.municipio.gob`, `educacion.municipio.gob`, `turismo.municipio.gob`, `cultura.municipio.gob`, `ambiente.municipio.gob`.
- Portal → Parámetros → Comportamiento → tildar “Solo datos” para este bot.
- Por entorno (opcional global): `WEBCHATBOT_GROUNDED_ONLY=1`.

## 4) Flujo de decisión actualizado
1) Reglas (FAQ/Smalltalk) → responden si hacen match.
2) RAG (intent=rag) → responde si similitud ≥ `rag_threshold`.
3) Fallback (nuevo):
   - Calcula top‑k pasajes (k=3). Si existen y superan ~90% del umbral, construye un prompt “CON TEXTO” y recién ahí llama al LLM.
   - Si no hay contexto y `grounded_only=true`, se abstiene (sugiere “ayuda”).

## 5) Cómo agregar cobertura (paso a paso)
### 5.1 Respuestas rápidas (Reglas)
- Portal → Parámetros → “Editar reglas…”.
- Cargar:
  - Keywords: “stems” (ej.: `licenc`, `conduc`).
  - Respuesta: breve + enlace oficial.
  - Origen: `faq` o `fallback`.
  - Min matches (opcional): número mínimo de keywords (k‑de‑n) para reducir falsos positivos.
- Persistencia: `chatbots/<id>/settings.json > rules[]`.

Ejemplo (proveedores):
```
{
  "enabled": true,
  "keywords": ["proveedor", "inscrip", "compra"],
  "min_matches": 2,
  "response": "La inscripción de proveedores se realiza en proveedores.municipio.gob o en Atención Vecinal.",
  "source": "faq"
}
```

### 5.2 RAG — Entradas JSON (FAQs enriquecidas)
- Editar `knowledge/faqs/municipal_faqs.json` (JSONC):
```
{
  "uid": "vc-009",
  "question": "¿Cómo me inscribo como proveedor municipal?",
  "answer": "Completá el registro y adjuntá documentación en proveedores.municipio.gob o en Atención Vecinal.",
  "tags": ["proveedor", "inscripcion", "inscribo", "inscribir", "compra", "registro"]
}
```
- Reiniciar la API para reindexar.

### 5.3 RAG — Textos curatoriales (`.txt`)
- Colocar/editar archivos `.txt` en `00relevamientos_j2/munivilladata/`.
- Heurística de indexación:
  - Divide por párrafos (líneas en blanco).
  - Ignora párrafos cortos (< ~160 caracteres).
  - `question`: primera oración/120 caracteres del párrafo.
  - `answer`: el párrafo completo.
  - `tags`: a partir del nombre del archivo.
- Reiniciar la API.

### 5.4 Clasificador de intents (orientar a RAG)
- `services/orchestrator/intent_classifier.py`: añadir patrones `IntentPattern(intent="rag", keywords=(...))` para consultas recurrentes (ej.: `("tramit", "online")`, `("proveedor", "inscrib")`).

## 6) Ajustes y tuning
- `rag_threshold` (0.26–0.32):
  - Más bajo → más recall (posibles FP).
  - Más alto → más precisión (posibles FN).
- Reglas: usar `min_matches` para temas con varias palabras.
- `grounded_only`:
  - ON: no LLM sin contexto.
  - OFF: LLM sin contexto (se mantiene compose()/pre_prompts) cuando no haya pasajes.

## 7) Ejemplos de interacción
- “trámites online” → RAG (JSON) o LLM con contexto (si el top‑k trae pasajes).
- “inscribirme como proveedor” → RAG (JSON) / Regla con min_matches=2; LLM con contexto si hiciera falta.
- “punto violeta” → RAG (JSON/TXT) → respuesta oficial breve.
- Sin cobertura y grounded_only=true → “No hay información precisa… escribí ‘ayuda’”.

## 8) Referencias
- Fallback con contexto: `services/orchestrator/service.py` (método `_fallback`).
- Top‑k: `services/orchestrator/rag.py` (método `topk`).
- Toggle UI: `frontend/index.html` + `frontend/portal.js`.
- Settings por bot: `services/chatbots/models.py` (campo `grounded_only`).
