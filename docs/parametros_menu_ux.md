# Menú de Parámetros (con Submenús) — Especificación UX/Dev

Este documento define un menú de parámetros completo (con subventanas) que cubre toda la parametrización soportada hoy y extensiones propuestas. Incluye mapeo a archivos/paths, pasos para editar cada caso y diagramas ASCII de navegación.

## Objetivo
- Centralizar configuración por bot en una UI clara y estratificada.
- Distinguir parámetros por bot (persisten en `chatbots/<id>/settings.json`) de parámetros globales (LLM/env).
- Ofrecer subventanas dedicadas para ediciones complejas (Reglas, RAG, Intents y Ayuda) manteniendo la ventana principal simple.

## Estructura del Menú (vista de “Parámetros” en el Portal)

```
Parámetros (Bot: municipal)
├─ 1) General
│   ├─ Grounded only (solo datos)
│   ├─ Usar reglas/FAQ
│   ├─ Usar RAG
│   ├─ Incluir reglas predefinidas
│   └─ RAG threshold
├─ 2) Generación (LLM)
│   ├─ Temperature
│   ├─ Top‑p
│   ├─ Max tokens
│   └─ Pre‑prompts (editor inline)
├─ 3) Reglas (FAQ/Fallback)
│   ├─ Abrir “Editor de reglas…” (subventana)
│   ├─ Respuesta genérica (no‑match): ON/OFF
│   │   ├─ Lista de respuestas
│   │   └─ Estrategia (first/random)
│   └─ Ver resumen (conteo/primeras keywords)
├─ 4) RAG (Base de conocimiento)
│   ├─ Ver estado (entradas JSON / TXT, fechas)
│   ├─ Abrir “Editor RAG (JSON)” (propuesto)
│   ├─ Abrir “Gestor RAG (TXT)” (propuesto)
│   └─ Botón Reindexar (propuesto)
├─ 5) Menú del Portal (chips)
│   ├─ Editor de chips (label + message, orden)
│   └─ (btn) Usar chips por defecto
├─ 6) Ayuda / Menú del bot (propuesto)
│   ├─ Plantilla de “ayuda/menu” (texto configurable)
│   └─ Vista previa (render)
├─ 7) Intents (propuesto)
│   ├─ Vista patrones actuales (solo lectura)
│   └─ Editor de patrones (alta/baja/orden) (propuesto)
└─ 8) Avanzadas / Sistema
    ├─ Ver/editar grounded_only (por bot)
    ├─ Variables globales (solo lectura): LLM_MODEL_PATH, WEBCHATBOT_TEXT_KB_DIR, WEBCHATBOT_GROUNDED_ONLY
    └─ Link a documentación (LLM y KB)
```

## Subventanas

1) Editor de reglas (existe)
- Campos por regla: enabled, source (faq/fallback), keywords (coma‑separadas, stems), min_matches (k‑de‑n), response (textarea).
- Persistencia: `settings.rules[]`.
- Mapeo: `chatbots/<id>/settings.json: rules[]`.

2) Editor RAG (JSON) (propuesto)
- Tabla de entradas: uid, question, tags (chips), (botón) editar answer (modal secundaria).
- Acciones: crear/editar/eliminar; guardar (PUT) a un endpoint `/rag/faqs` (propuesto) que escriba `knowledge/faqs/municipal_faqs.json` (JSONC sin comentarios durante PUT) y dispare reindex.
- Mapeo: `knowledge/faqs/municipal_faqs.json`.

3) Gestor RAG (TXT) (propuesto)
- Vista de archivos `.txt` en `WEBCHATBOT_TEXT_KB_DIR` (default: `00relevamientos_j2/munivilladata`).
- Acciones: subir/borrar archivo (multipart) y botón “Reindexar”.
- Nota: requiere endpoints nuevos seguros.

4) Editor de Ayuda/Menu (propuesto)
- Campo “plantilla de ayuda” (textarea; markdown simple); tokens sugeridos para chips/atajos.
- Mapeo propuesto: `settings.help_template` (string); fallback → reglas default en código si vacío.

5) Editor de Intents (propuesto)
- Tabla de `IntentPattern`: intent, keywords[], confidence.
- Acciones: orden arriba/abajo, crear/eliminar.
- Mapeo propuesto: endpoint `/intents` que guarde un YAML/JSON en `chatbots/<id>/intents.json` (o global `config/intents.json`).

## Mapeo UI → JSON / Código

- General
  - grounded_only → `settings.grounded_only` (bool)
  - use_rules → `settings.features.use_rules` (bool)
  - use_rag → `settings.features.use_rag` (bool)
  - enable_default_rules → `settings.features.enable_default_rules` (bool)
  - rag_threshold → `settings.rag_threshold` (float)

- Generación (LLM)
  - temperature → `settings.generation.temperature`
  - top_p → `settings.generation.top_p`
  - max_tokens → `settings.generation.max_tokens`
  - pre_prompts → `settings.pre_prompts[]`

- Reglas
  - rules[] → `settings.rules[]`
  - no_match → `settings.features.use_generic_no_match`
  - no_match_replies → `settings.no_match_replies[]`
  - no_match_pick → `settings.no_match_pick`

- RAG
  - JSON (read‑only hoy): `knowledge/faqs/municipal_faqs.json`
  - TXT (read‑only hoy): `00relevamientos_j2/munivilladata/` (o `WEBCHATBOT_TEXT_KB_DIR`)

- Menú del Portal
  - chips → `settings.menu_suggestions[]`

- Avanzadas / Sistema
  - Variables globales via env: `LLM_MODEL_PATH`, `WEBCHATBOT_TEXT_KB_DIR`, `WEBCHATBOT_GROUNDED_ONLY`.

## Diagrama de navegación (ASCII)

```
Parámetros
├─ General
│  ├─ [ ] Grounded only
│  ├─ [ ] Usar reglas/FAQ
│  ├─ [ ] Usar RAG
│  ├─ [ ] Incluir reglas predefinidas
│  └─ RAG threshold: [ 0.28 ]
├─ Generación (LLM)
│  ├─ Temperature: [0.70]
│  ├─ Top‑p:       [0.90]
│  ├─ Max tokens:  [200]
│  └─ Pre‑prompts: [+ Agregar línea]
├─ Reglas
│  ├─ (btn) Editar reglas… → [Subventana: lista de reglas]
│  ├─ [ ] Respuesta genérica (no‑match)
│  │   ├─ (lista) respuestas
│  │   └─ Estrategia: (first|random)
│  └─ (resumen) 7 reglas activas
├─ RAG
│  ├─ Estado: JSON=25 entradas; TXT=3 archivos
│  ├─ (btn) Editor RAG (JSON)… (propuesto)
│  ├─ (btn) Gestor RAG (TXT)… (propuesto)
│  └─ (btn) Reindexar (propuesto)
├─ Menú del Portal (chips)
│  └─ (lista) label + message [+ Agregar]
├─ Ayuda/Menu (propuesto)
│  ├─ Plantilla ayuda/menu (textarea)
│  └─ Vista previa
├─ Intents (propuesto)
│  ├─ (tabla) intent, keywords, confidence
│  └─ (botones) mover/crear/eliminar
└─ Avanzadas / Sistema
   ├─ grounded_only (por bot)
   ├─ LLM_MODEL_PATH (env)
   ├─ WEBCHATBOT_TEXT_KB_DIR (env)
   └─ WEBCHATBOT_GROUNDED_ONLY (env)
```

## Paso a paso: editar cada caso

- Cambiar Grounded only (solo datos)
  1) Parámetros → General → marcar “Grounded only”.
  2) Guardar. Efecto: si no hay contexto, el bot se abstiene de invocar LLM.

- Ajustar generación (LLM)
  1) Parámetros → Generación. Ajustar temperature/top_p/max_tokens.
  2) `pre_prompts`: agregar líneas de estilo/seguridad.

- Agregar regla rápida
  1) Parámetros → Reglas → “Editar reglas…”.
  2) Cargar keywords (stems), min_matches (opcional), respuesta y origen.
  3) Guardar. Efecto inmediato.

- Añadir entrada RAG (JSON)
  1) Editar `knowledge/faqs/municipal_faqs.json` (JSONC). Ver ejemplo de estructura.
  2) Reiniciar API para reindexar. Probar consulta.

- Añadir entrada RAG (TXT)
  1) Colocar `.txt` en `00relevamientos_j2/munivilladata/` (párrafos > ~160 chars).
  2) Reiniciar API para reindexar. Probar consulta.

- Cambiar chips del Portal
  1) Parámetros → Menú del Portal. Agregar/eliminar/ordenar chips.
  2) (Opcional) “Usar chips por defecto” para restablecer los valores de fábrica.
  3) Guardar. Ver cambios en la vista municipal.

- (Propuesto) Editar Ayuda/Menu
  1) Parámetros → Ayuda/Menu. Cargar plantilla (texto/markdown simple).
  2) Guardar. El bot usará esta plantilla para “ayuda/menu”.

- (Propuesto) Editar Intents
  1) Parámetros → Intents. Ajustar patrones (keywords / confidence, orden).
  2) Guardar. El clasificador se reconfigura sin reinicio.

## Consideraciones
- Ciertos ítems (RAG JSON/TXT y Intents) requieren endpoints nuevos para editar desde UI; hoy se manejan por archivos y reinicio.
- Mantener `tags` de RAG en minúscula y sin tildes; usar stems en reglas.
- Cambios de KB requieren reiniciar la API para reindexar.
