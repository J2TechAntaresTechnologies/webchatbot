# Operación y Configuración del Chatbot Municipal

Este documento resume, con foco práctico, dónde viven los prompts y parámetros, cómo se configuran los chatbots (municipal y MAR2), qué se persiste en disco, cómo influyen los logs y parámetros en el comportamiento, y buenas prácticas para administrar prompts y archivos relacionados.

## 1) Dónde se alojan prompts, parámetros y archivos persistentes

- Orquestación de prompts
  - El orquestador inyecta `pre_prompts` antes del mensaje del usuario cuando llama al LLM.
  - Implementación: `services/orchestrator/service.py` (función interna `compose_with_preprompts`).
  - Se usa en:
    - Canal libre (`mar2`/`free`): siempre LLM con `pre_prompts` si existen.
    - Canal municipal (`web`): primero Reglas/FAQ → RAG → si no resuelven, LLM con `pre_prompts`.

- Configuración persistente por bot
  - Archivo: `chatbots/<id>/settings.json` (se crea/actualiza vía API o Portal).
  - Esquema (modelo): `services/chatbots/models.py` → `BotSettings` con:
    - `generation`: `temperature`, `top_p`, `max_tokens` (con límites y clamp de seguridad).
    - `features`: `use_rules` (FAQ/reglas), `use_rag`, `use_generic_no_match` (respuesta genérica), `enable_default_rules` (incluir/excluir reglas por defecto).
    - `menu_suggestions`: chips de atajos para el cliente municipal.
    - `pre_prompts`: lista de instrucciones a inyectar antes del mensaje.
    - `no_match_replies`: lista de frases genéricas (“no entendí”).
    - `no_match_pick`: estrategia para elegir la genérica (`first` o `random`).
    - `rules`: lista de reglas personalizadas (`{enabled, keywords[], response, source}`) para sumar (o reemplazar, si deshabilitás las default).

- Endpoints de configuración (persisten en disco)
  - GET `/chatbots/{id}/settings?channel=...` → lee settings (con defaults si no hay archivo).
  - PUT `/chatbots/{id}/settings` → guarda `settings.json` en `chatbots/<id>/`.
  - POST `/chatbots/{id}/settings/reset?channel=...` → restablece a defaults.

- Base de conocimiento (RAG)
  - Dataset por defecto: `knowledge/faqs/municipal_faqs.json` (admite comentarios JSONC). Además, se indexan `.txt` curatoriales desde `00relevamientos_j2/munivilladata` al iniciar la API.
  - Carga/uso: `services/orchestrator/rag.py` (umbral de similitud léxica por defecto `0.28`).
  - El loader elimina comentarios antes de parsear; herramientas como `jq` no soportan comentarios.

- Logs y persistencia de conversaciones (estado actual)
  - No se guardan transcripts de conversación ni prompts/completions en disco o BD.
  - El adaptador LLM registra avisos/errores a stdout (Uvicorn/console): `services/llm_adapter/client.py` (logger).
  - Para reducir ruido de logs al ejecutar modelos GGUF (llama.cpp), podés usar el script `./start_noverbose.sh`, que ajusta `GGML_LOG_LEVEL=ERROR` / `LLAMA_LOG_LEVEL=ERROR` y baja el nivel de Uvicorn.

## 2) Configuración de chatbots: consejos y tutorial paso a paso

- Desde el Portal (recomendado, sin tocar archivos)
  1. Abrí `frontend/index.html` (servido, por ejemplo, con `python -m http.server --directory frontend 5173`).
  2. Clic en Configuración de la tarjeta del bot (Municipal o MAR2).
  3. Ajustá:
     - Generación: `temperature`, `top_p`, `max_tokens` (valores válidos: T [0.0–2.0], P [0.0–1.0], M ≥ 1).
     - Comportamiento: `usar reglas` (FAQ/reglas), `usar RAG`, `RAG threshold` (umbral 0–1, recomendado 0.20–0.40), `respuesta genérica`, `incluir reglas por defecto`.
     - Menú (solo municipal): etiquetas y mensajes para chips.
     - Pre-prompts: agrega instrucciones, una por fila (se inyectan como lista con viñetas).
     - Visibilidad del Portal: en la Configuración de tema (botón "Configuración" en la barra superior del Portal), tildá o destildá "Mostrar modo libre (MAR2) en el portal" para ocultar esa variante de la pantalla principal.
     - Reglas personalizadas: alta/baja/edición de `keywords` (separadas por coma), `response` (texto) y `source` (`faq` o `fallback`) por regla. Podés eliminar reglas desde el botón ✕. Comportamiento: si `Incluir reglas predefinidas` está activo, se aplican tus reglas primero (prioridad) y luego `DEFAULT_RULES`. Si está desactivado, solo tus reglas.
     - Respuesta genérica (solo Municipal): activá “Responder genérico si no hay coincidencia” y cargá múltiples textos genéricos (una fila por respuesta). Elegí la estrategia: `Siempre la primera` o `Al azar`.
     - (Clasificación a RAG) Para que ciertas consultas ejecuten RAG, edita `services/orchestrator/intent_classifier.py` y agrega `IntentPattern(intent="rag", keywords=(...))` con stems relevantes (ej.: `( "ambiente", "permis" )`, `( "poda", )`).
  4. Guardar (PUT) o Restablecer (POST reset). Esto crea/actualiza `chatbots/<id>/settings.json`.

- Vía API (curl)
  - Leer settings actuales:
    ```bash
    curl -sS "http://127.0.0.1:8000/chatbots/municipal/settings?channel=web" | jq .
    ```
- Guardar settings:
    ```bash
    curl -sS -X PUT \
      "http://127.0.0.1:8000/chatbots/municipal/settings" \
      -H 'Content-Type: application/json' \
      -d '{
            "generation": {"temperature": 0.7, "top_p": 0.9, "max_tokens": 256},
            "features": {
              "use_rules": true,
              "use_rag": true,
              "use_generic_no_match": true,
              "enable_default_rules": true
            },
            "menu_suggestions": [
              {"label": "Pagar impuestos", "message": "¿Cómo pago mis impuestos?"}
            ],
            "pre_prompts": [
              "Responde con tono claro y conciso",
              "Si hay trámites, sugiere el canal oficial"
            ],
            "no_match_replies": [
              "No pude comprender tu consulta. Escribí 'ayuda' para ver opciones o contame en pocas palabras qué necesitás."
            ],
            "no_match_pick": "first",
            "rules": [
              {"enabled": true, "keywords": ["turno", "reprogram"], "response": "Podés reprogramar tu turno en turnos.municipio.gob.", "source": "faq"}
            ]
          }' | jq .
    ```
  - Restablecer defaults:
    ```bash
    curl -sS -X POST "http://127.0.0.1:8000/chatbots/municipal/settings/reset?channel=web" | jq .
    ```

- Editando archivos directamente (cuando no hay API)
  - Editá `chatbots/municipal/settings.json` respetando la estructura de `BotSettings`.
  - Mantén valores dentro de los límites; al cargar, el backend “clampa” números fuera de rango.

- Consejos prácticos
  - Municipal (informativo): `temperature` 0.6–0.8, `top_p` 0.8–0.95, `max_tokens` 200–400; `use_rules=true`, `use_rag=true`; evaluar `use_generic_no_match=true` para UX más guiada.
  - MAR2 (creativo): `temperature` 0.8–1.1, `top_p` 0.9–1.0; normalmente `use_rules=false`, `use_rag=false`.
  - Cambiá un parámetro por vez; validá con preguntas reales y medí latencia.

### 2.1 Tutorial: Parámetros “Municipal” (sección completa)

1) Generación
- `Temperature`, `Top‑p`, `Max tokens`: controlan la variabilidad y longitud cuando el flujo cae al LLM.

2) Comportamiento
- `Usar reglas/FAQ`: activa coincidencias determinísticas (saludos, ayuda, pagos, etc.).
- `Usar RAG`: permite consultar el dataset `knowledge/faqs/municipal_faqs.json` cuando el intent es `rag`.
- `Incluir reglas predefinidas del sistema`: si está apagado, se ignora el set por defecto y solo se usan las reglas personalizadas.

3) Respuesta genérica (no‑match)
- Toggle “Responder genérico si no hay coincidencia”.
- Lista de respuestas genéricas: agregá múltiples frases; se aplican cuando no hay match de reglas y/o el intent es `unknown` (según settings).
- Estrategia: `Siempre la primera` (determinístico) o `Elegir una al azar` (aleatorio entre las cargadas).

4) Reglas personalizadas
- Por cada regla definís:
  - `Keywords` (separadas por coma). Se matchea por subcadena sobre texto normalizado (minúsculas, sin tildes).
  - `Respuesta` (texto devuelto).
  - `Origen` (`faq` o `fallback`) para trazabilidad.
- El botón “Eliminar” quita la regla de la UI. Al guardar se persiste en el servidor.
- Comportamiento: si `Incluir reglas predefinidas` está activo, se aplican `DEFAULT_RULES` + tus reglas; si está desactivado, solo tus reglas.

5) Guardar y Restablecer
- “Guardar” persiste en `chatbots/<id>/settings.json` y tiene efecto inmediato en el backend.
- “Restablecer” vuelve a los valores estándar del sistema para esa variante.

Notas
- RAG threshold controla la sensibilidad de recuperación: más bajo ⇒ más resultados (y riesgo de falsos positivos); más alto ⇒ menos resultados pero más precisos. Si no estás seguro, usar 0.28.
- Tras editar `municipal_faqs.json`, reiniciá la API para reindexar el dataset.

## 3) Cómo afectan logs y parámetros al bot

- Parámetros de generación (LLM)
  - `temperature`: mayor ⇒ más variación y creatividad; menor ⇒ más estabilidad y menor riesgo de alucinación.
  - `top_p`: acota el muestreo al “núcleo” de probabilidad (0.6–0.9 conservador; 0.9–1.0 más diverso).
  - `max_tokens`: límite de longitud de respuesta. Afecta latencia; valores muy bajos pueden truncar.

- Toggles de comportamiento
  - `use_rules=true`: prioriza respuestas curadas (horarios, “ayuda”, etc.). Reduce llamados al LLM.
  - `use_rag=true`: habilita búsqueda en `knowledge/faqs/municipal_faqs.json`; mejora precisión en temas cubiertos.
  - `enable_default_rules=false`: desactiva el set de reglas por defecto; el motor usará únicamente las reglas personalizadas que definas en el Portal.
  - `use_generic_no_match=true`: ante no‑match, responde con una de las frases en `no_match_replies`. Si `no_match_pick=random`, elige una al azar; si `first`, usa la primera.
  - Desactivarlos transfiere más carga al LLM y puede aumentar latencia/costo y riesgo de alucinación.

- Logs (estado actual)
  - El proyecto no persiste conversaciones; el logger del LLM escribe a consola (stdout). Esto no cambia la respuesta del bot, pero ayuda a diagnosticar fallos de modelo o configuración.
  - Recomendado para producción: habilitar auditoría (inputs/outputs, métricas) con cuidado de PII, retención y consentimiento. Una estrategia común es JSONL rotado (por ejemplo, `logs/audit-YYYYMMDD.jsonl`).

## 4) Guía de prompts: configuración, estrategias y gestión de archivos

- Dónde configurar prompts
  - `pre_prompts` por bot en `chatbots/<id>/settings.json`: lista de instrucciones tipo “guía de estilo” o “políticas” que se anteponen al mensaje del usuario.
  - Mantén cada instrucción breve y accionable; el orquestador las serializa como viñetas.

- Estrategias efectivas
  - “Marco de rol”: define claramente el rol (p. ej., “Agente municipal de atención al público”).
  - “Instrucciones de seguridad”: evitar inventar; priorizar fuentes oficiales; derivar a humano cuando falte información.
  - “Estilo y formato”: tono claro, enlaces oficiales, pasos numerados cuando aplique.
  - “Restricciones”: no pedir datos sensibles; verificar que los links sean del dominio oficial.

- Gestión y versionado
  - Versioná los cambios en `chatbots/<id>/settings.json` (commit/PR) y documentá el motivo del ajuste.
  - Para experimentos, trabajá en una rama con un `<id>` alternativo (p. ej. `municipal-dev`) con su propio `settings.json`.
  - Si necesitás prompts extensos, considera dividirlos en varias entradas de `pre_prompts` (cada línea una instrucción) en lugar de un bloque largo.

- Archivos nuevos sugeridos (opcionales)
  - `chatbots/<id>/prompts/` (plantillas y notas internas) para trabajo editorial; el backend actual no los lee automáticamente, pero facilita organización y revisión.
  - Documentá convenciones (nombres, autoría, fecha, objetivo) en un `README.md` dentro de la carpeta del bot.

- Validación
  - Tras cambios de prompts/params, probá con un set de preguntas de regresión (horarios, trámites, contacto, normativa) y verificá que Reglas/RAG sigan resolviendo antes del LLM.
  - Medí latencia y claridad de respuestas; ajustá `temperature/top_p` si observás divagación o respuestas demasiado secas.

## Apéndice: rutas y referencias rápidas

- Endpoint de chat: `POST /chat/message` (payload `ChatRequest` con `session_id`, `message`, `channel`, `bot_id`).
- Configuración por bot (persistencia): `GET|PUT|POST reset /chatbots/{id}/settings`.
- Esquemas: `services/orchestrator/schema.py` y `services/chatbots/models.py`.
- Reglas FAQ: `services/orchestrator/rule_engine.py`.
- RAG (dataset por defecto): `knowledge/faqs/municipal_faqs.json`.
- Adaptador LLM y logs: `services/llm_adapter/client.py` (stdout).
