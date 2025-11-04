# Manual de Aprendizaje y Modificaciones

Este manual orienta a nuevas personas del equipo para comprender, extender y mantener el chatbot municipal.

---

## 1. Ruta de aprendizaje sugerida

1. **Contexto general**
   - Leer `README.md` para entender el alcance y los componentes activos.
   - Revisar `docs/architecture.md` para ubicar cada módulo en el flujo end-to-end.
2. **Manos a la obra (día 1)**
   - Crear entorno virtual y ejecutar `make install-dev`.
   - Levantar la API (`uvicorn services.api.main:app --reload`) y el frontend (`python -m http.server --directory frontend 5173`).
   - Probar consultas típicas: horarios, reclamos, ordenanzas.
3. **Profundizar (semana 1)**
   - Leer las pruebas unitarias en `tests/unit/` y añadir un caso nuevo.
   - Explorar el orquestador (`services/orchestrator`) y el dataset RAG.
4. **Especialización (posterior)**
   - Elegir una línea del roadmap (`docs/roadmap.md`) y diseñar un spike corto.
   - Preparar documentación adicional tras cada cambio significativo.

---

## 2. Arquitectura y responsabilidades

| Módulo | Ubicación | Responsabilidad principal |
| --- | --- | --- |
| API | `services/api/main.py` | Exponer endpoints FastAPI, validar payloads, gestionar middlewares. |
| Orquestador | `services/orchestrator/` | Clasificar intents, ejecutar reglas, invocar RAG/LLM, decidir handoff. |
| LLM Adapter | `services/llm_adapter/` | Encapsular proveedor LLM (hoy devuelve placeholder). |
| Knowledge | `knowledge/` | Organizar fuentes, ETL y datasets para RAG. |
| Frontend | `frontend/` | Interfaz web que consume el endpoint `/chat/message`. |

El orquestador está diseñado para ser extensible: cada "fuente" (reglas, RAG, LLM) puede evolucionar sin romper las otras.

---

## 3. Flujo de desarrollo recomendado

1. **Crear rama personal / issue** (si trabajás con Git).
2. **Activar entorno virtual**: `source bin/activate` o usar herramientas favoritas; el script `scripts/export_webchatbot_env.sh` exporta `PYTHONPATH` y rutas de modelo al hacerlo.
3. **Instalar dependencias**: `make install-dev` (incluye pruebas) y `make install-rag` cuando se requieran componentes avanzados.
4. **Ejecutar pruebas** antes y después de cada cambio: `make test` o `./bin/python -m pytest` desde la raíz.
5. **Documentar** las decisiones clave en `docs/` o como comentarios puntuales.
6. **Solicitar revisión** incluyendo captura de pruebas y decisiones de diseño.

---

## 4. Modificar el orquestador

### 4.1 Añadir nuevos intents
1. Editar `services/orchestrator/intent_classifier.py`.
2. Agregar un `IntentPattern` con las keywords y confianza deseadas.
3. Si el intent requiere nueva ruta de respuesta, extender `ChatOrchestrator.respond()` y crear un método `_try_<fuente>` siguiendo el patrón existente.
4. Incluir pruebas unitarias específicas en `tests/unit/test_orchestrator_basic.py` o un archivo nuevo.

### 4.2 Sustituir el motor de reglas
- Las reglas actuales viven en `services/orchestrator/rule_engine.py`.
- Para cargar reglas desde persistencia (YAML/DB), crear un loader y pasar la colección al inicializar `RuleBasedResponder`.
- Mantener la función `normalize_text` para coincidencias consistentes.

### 4.3 Integrar un RAG real
1. Generar embeddings y almacenar en `knowledge/embeddings/`.
2. Implementar un adaptador que cumpla `RagResponderProtocol` (`services/orchestrator/types.py`).
3. Invocar `ChatOrchestrator.attach_rag(<tu adaptador>)` en el arranque de la API.
4. Actualizar `docs/manual_aprendizaje.md` y `docs/architecture.md` con la nueva arquitectura.

### 4.4 Conectar con un LLM
- Instalar dependencias avanzadas (`make install-rag`) para habilitar `llama-cpp-python` u otros conectores.
- El entorno virtual ejecuta `scripts/export_webchatbot_env.sh` al activarse y exporta un valor por defecto para `LLM_MODEL_PATH` (Gemma 3 1B `Q4_K_M`). Verificá compatibilidad con tu versión de `llama-cpp-python`.
- Para usar otro modelo, exportá `WEBCHATBOT_DEFAULT_LLM_MODEL_PATH` o `LLM_MODEL_PATH` **antes** de `source bin/activate`, o modifica el script según tus necesidades.
- Ajustar hiperparámetros con `LLM_MAX_TOKENS`, `LLM_TEMPERATURE`, `LLM_TOP_P` y `LLM_CONTEXT_WINDOW` según la capacidad del modelo.
- Mantener un mensaje placeholder como fallback cuando el modelo no esté disponible o falle la generación.
- Añadir manejo de errores, timeouts y saneamiento de prompts.
- Integrar moderación previa (ver sección 6) para bloquear contenido inapropiado.

### 4.5 Agregar una nueva variante al portal

1. Crear el directorio `chatbots/<id>/` y definir `config.json` con al menos:
   ```json
   { "id": "<id>", "name": "<Nombre>", "description": "<Descripción>", "channel": "web|mar2|...", "frontend_page": "<página>.html" }
   ```
2. Crear/duplicar una página en `frontend/` (por ejemplo `mi_variante.html`) y un script asociado si necesita comportamiento distinto.
3. Registrar la variante en `frontend/chatbots.json` para que aparezca en el Portal.
4. Si la variante requiere cambios del backend (reglas, RAG), agregarlos en `services/orchestrator` y cubrir con tests en `tests/unit/`.
5. Opcional: colocar modelos `.gguf` compartidos en `modelos/` para que el script de entorno los detecte automáticamente.

---

## 5. Trabajo con la base de conocimiento

1. **Formato del dataset**: usar JSON con campos `uid`, `question`, `answer`, `tags`.
2. **Normalización**: mantener respuestas oficiales y tono institucional.
3. **Automatización**: crear scripts `knowledge/etl_<fuente>.py` para convertir hojas de cálculo o PDFs.
4. **Validación**: agregar pruebas que verifiquen esquemas (puede usarse Pydantic o `jsonschema`).
5. **Versionado**: registrar fecha y fuente. Considerar Git LFS para documentos pesados.

---

## 6. Seguridad y compliance

- **Moderación**: implementar filtros antes de invocar LLM (listas de palabras, modelos de clasificación, detección de PII).
- **Registro**: loguear conversaciones con identificadores anónimos y métricas clave (latencia, intent, fuente de respuesta).
- **Privacidad**: limpiar PII de logs y aplicar políticas de retención.
- **Pruebas de robustez**: diseñar suites específicas contra prompt injection y jailbreaks.

---

## 7. Pruebas y calidad

- `pytest` con `pytest-asyncio` para rutas asíncronas.
- Cubrir casos felices, errores y regresiones de seguridad (por ejemplo, entradas vacías, payload inválido, timeout de LLM).
- Considerar `httpx.AsyncClient` para pruebas de contrato de la API.
- Añadir linters/formateadores (Ruff, Black) cuando se incorpore pipeline de CI.
- `tests/unit/test_orchestrator_basic.py` valida rutas principales del orquestador (reglas, RAG, handoff y fallback) y sirve como plantilla para nuevos casos.

---

## 8. Frontend: lineamientos

- Mantener accesibilidad (etiquetas `label`, roles ARIA, contraste).
- Centralizar configuración de API en un módulo único.
- Diseñar componentes reutilizables para mensajes, paneles y formularios.
- Añadir pruebas E2E con Playwright o Cypress al migrar a un framework moderno.

---

## 9. Entrega y despliegue

Aunque aún no existe pipeline CI/CD, se recomienda preparar:

1. Dockerfile para API y frontend.
2. `docker-compose` para orquestar API, redis/vector-store, frontend.
3. Workflow de GitHub Actions que instale dependencias, ejecute `make test` y publique artefactos.
4. Checklist de despliegue con validaciones de seguridad y monitoreo.

---

## 10. Recursos adicionales

- `docs/roadmap.md`: prioriza próximos hitos.
- `docs/architecture.md`: referencia visual y decisiones técnicas.
- Repos municipal ficticio para textos oficiales (pendiente de URL real).

Cualquier cambio significativo debe reflejarse en este manual y en la documentación asociada.
