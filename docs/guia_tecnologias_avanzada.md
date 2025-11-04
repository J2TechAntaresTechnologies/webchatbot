# Guia avanzada de tecnologias del Chatbot Municipal

## 1. Mapa tecnologico y responsabilidades

| Capa | Tecnologia principal | Rol en el proyecto | Referencias clave |
| --- | --- | --- | --- |
| Frontend web | HTML5, CSS, JavaScript vanilla | Renderiza interfaz accesible y consume la API `/chat/message` mediante `fetch`. | `frontend/index.html`, `frontend/app.js` |
| API Gateway | FastAPI + Uvicorn | Expone endpoints REST asincronicos, aplica CORS y orquesta el flujo de peticiones. | `services/api/main.py` |
| Modelado de datos | Pydantic v2 | Valida `ChatRequest` y `ChatResponse`, transforma payloads y garantiza tipos. | `services/orchestrator/schema.py` |
| Orquestador | Python async + IntentClassifier heuristico | Decide la fuente de respuesta (reglas, RAG, LLM, handoff). | `services/orchestrator/service.py`, `intent_classifier.py` |
| Reglas FAQ | Motor propio `RuleBasedResponder` | Resuelve FAQs y smalltalk mediante coincidencia lexical normalizada. | `services/orchestrator/rule_engine.py` |
| RAG ligero | `SimpleRagResponder` + JSON | Calcula similitud coseno sobre tokens normalizados para recuperar respuestas. | `services/orchestrator/rag.py`, `knowledge/faqs/municipal_faqs.json` |
| Integracion LLM | `llama-cpp-python` (opcional) + `LLMClient` | Ejecuta modelos GGUF locales y provee fallback placeholder. | `services/llm_adapter/client.py`, `services/llm_adapter/settings.py` |
| Configuracion | `pydantic-settings`, `.env`, script bash | Centraliza variables de entorno y expone rutas de modelo. | `scripts/export_webchatbot_env.sh` |
| Logging | `structlog` (via configuracion futura) | Provee trayectorias para trazabilidad estructurada. | `requirements/base.txt` |
| Pruebas | `pytest`, `pytest-asyncio`, `httpx` | Validan comportamiento del orquestador y endpoints. | `tests/unit/test_orchestrator_basic.py` |
| Observabilidad opcional | OpenTelemetry SDK/API | Encapsula spans y metricas cuando se activa `requirements/rag.txt`. | `requirements/rag.txt` |

## 2. Stack detallado por componente

### 2.1 Frontend estatico
- `frontend/index.html` carga `frontend/app.js`, que genera un `sessionId` con `crypto.randomUUID` y envios `fetch` asincronicos.
- `app.js` detecta entorno local (`window.location.port === "5173"`) y redirige las peticiones a `http://127.0.0.1:8000`.
- `styles.css` contiene estilos basicos y puede reemplazarse por cualquier framework CSS sin afectar la API.

**Buenas practicas**
- Mantener el formulario accesible (elementos `label` y atributos ARIA).
- Reutilizar `appendMessage` para instrumentar efectos (por ejemplo, eventos de analytics) antes de renderizar.

### 2.2 API Gateway con FastAPI
- `services/api/main.py` crea la aplicacion con `FastAPI(title="Chatbot Municipal", version="0.1.0")` y expone el router del orquestador.
- Se activa `CORSMiddleware` para permitir origenes locales (`localhost`, `127.0.0.1`, `0.0.0.0` en puerto 5173).
- Uvicorn actua como servidor ASGI (`uvicorn services.api.main:app --reload`).

**Puntos avanzados**
1. Integrar seguridad municipal agregando middlewares JWT u OAuth2 sobre el objeto `app`.
2. Aplicar rate limiting usando dependencias (`slowapi`, `redis`) y el router `APIRouter`.
3. Habilitar OpenAPI y documentacion interactiva en `/docs` para negociar contratos con otras areas.

### 2.3 Modelado con Pydantic v2
- `services/orchestrator/schema.py` define `ChatRequest` y `ChatResponse` con `BaseModel`.
- Pydantic v2 habilita serializacion eficiente (por ejemplo `model_dump_json`) y validacion estricta con anotaciones `Literal` para `source`.

**Recomendaciones**
- Usar `@model_validator(mode="after")` si se agregan campos derivados.
- Configurar `model_config = ConfigDict(extra="forbid")` para bloquear claves inesperadas cuando se abra la API a clientes externos.

### 2.4 Orquestador central
- `ChatOrchestrator` (`services/orchestrator/service.py`) maneja el pipeline: clasifica intent, intenta reglas, consulta RAG y recurre al LLM.
- `IntentClassifier` combina patrones (`IntentPattern`) con coincidencia lexical sobre texto normalizado (`text_utils.normalize_text`).
- `RuleBasedResponder` (archivo homonimo) almacena respuestas deterministicas (`faq`, `smalltalk`) y delega a la normalizacion.

**Extensiones tipicas**
1. Reemplazar heuristicas por un modelo ML ligero; crear adaptador que cumpla `IntentClassifierProtocol`.
2. Conectar bases de datos u ORMs para persistir sesiones antes de devolver la respuesta (utilizar SQLAlchemy del paquete opcional `requirements/rag.txt`).
3. Enriquecer `IntentPrediction` con puntuaciones y explicar decisiones (tracing via `structlog`).

### 2.5 Recuperacion aumentada (RAG)
- `SimpleRagResponder` tokeniza texto normalizado, calcula TF y usa similitud coseno (`_cosine_similarity`).
- `load_default_entries` ingiere JSON (`knowledge/faqs/municipal_faqs.json`) y crea `KnowledgeEntry` via dataclass.

**Upgrade path**
1. Reemplazar `_embed_text` por embeddings densos (SentenceTransformers) y vector store (ChromaDB, PostgreSQL + PGVector).
2. Ajustar `threshold` para controlar precision/recall; incorporar scoring hibrido (BM25 + embeddings).
3. Añadir metadata en `KnowledgeEntry.tags` para filtrar por area municipal antes de calcular similitud.

### 2.6 Integracion LLM
- `LLMClient` intenta inicializar `llama_cpp.Llama` usando rutas provistas por `LLMSettings` (var de entorno `LLM_MODEL_PATH`).
- `scripts/export_webchatbot_env.sh` exporta `WEBCHATBOT_PROJECT_ROOT`, agrega el repo a `PYTHONPATH` y define un modelo GGUF por defecto (`WEBCHATBOT_DEFAULT_LLM_MODEL_PATH`).
- Si no se encuentra el modelo o `llama-cpp-python`, la respuesta vuelve a `PLACEHOLDER_REPLY`, garantizando resiliencia.

**Sugerencias avanzadas**
1. Activar stream de tokens llamando `self._llama.create_completion(stream=True)` y transformando la ruta `/chat/message` a streaming (FastAPI `EventSourceResponse`).
2. parametrizar hiperparametros via variables de entorno (`LLM_MAX_TOKENS`, `LLM_TEMPERATURE`, `LLM_TOP_P`, `LLM_CONTEXT_WINDOW`).
3. Envolver `generate` con moderacion (clasificadores de toxicidad) antes de aceptar la respuesta generada.

### 2.7 Configuracion y despliegue
- `Makefile` (objetivos `install-dev`, `install-rag`, `test`).
- `start.sh` puede orquestarse desde systemd o contenedores (Dockerfile pendiente).
- `docs/roadmap.md` detalla integraciones de observabilidad y CI/CD planificadas.

## 3. Tutorial paso a paso para operar y extender el stack

### 3.1 Preparacion del entorno
1. Clonar el repositorio y posicionarse en la raiz.
2. Activar el entorno virtual incluido: `source bin/activate`.
3. Ejecutar el script de entorno (se invoca automaticamente al activar el venv, pero puede hacerse manualmente):
   ```bash
   source scripts/export_webchatbot_env.sh
   ```
4. Instalar dependencias minimas: `pip install -r requirements.txt`.
5. Para desarrollo completo, incluir pruebas: `pip install -r requirements/dev.txt`.
6. Cuando se requiera RAG avanzado o LLM, instalar extras: `pip install -r requirements/rag.txt`.

### 3.2 Levantar servicios
1. **API**: `uvicorn services.api.main:app --reload`.
2. **Frontend** (opcional): `python -m http.server --directory frontend 5173`.
3. Abrir `http://localhost:5173` y enviar mensajes; verificar consola del terminal para logs de Uvicorn.

### 3.3 Personalizar la base de conocimiento
1. Editar `knowledge/faqs/municipal_faqs.json` agregando entradas con campos `uid`, `question`, `answer`, `tags`.
2. Reiniciar la API para que `ChatOrchestrator._bootstrap_rag()` recargue las nuevas entradas.
3. Ajustar `threshold` del `SimpleRagResponder` si se observa ruido en las respuestas.

### 3.4 Añadir un intent nuevo
1. Agregar un `IntentPattern` en `services/orchestrator/intent_classifier.py`.
2. Implementar la ruta de respuesta en `ChatOrchestrator` (por ejemplo, `_try_transversal`).
3. Escribir pruebas en `tests/unit/test_orchestrator_basic.py` cubriendo el flujo.
4. Ejecutar `pytest` para validar.

### 3.5 Conectar un modelo LLM real
1. Descargar un modelo GGUF compatible (`llama.cpp`).
2. Exportar ruta personalizada antes de activar el venv:
   ```bash
   export WEBCHATBOT_DEFAULT_LLM_MODEL_PATH=/ruta/al/modelo.gguf
   ```
3. Activar el entorno y verificar que `LLM_MODEL_PATH` exista (el script emite un warning si falta el archivo).
4. Instalar `llama-cpp-python` (`make install-rag`).
5. Probar generacion enviando mensajes que no caigan en reglas ni RAG (por ejemplo, "Cuentame algo sobre tecnologia").

### 3.6 Encender observabilidad
1. Instalar dependencias (`pip install -r requirements/rag.txt`).
2. Configurar variables OpenTelemetry (`OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME=webchatbot-api`).
3. Instrumentar FastAPI usando `opentelemetry-instrument uvicorn ...` o integrar manualmente en `create_app()`.

## 4. Licencias y consideraciones para uso comercial

> Nota: verifica siempre las licencias oficiales antes de desplegar en produccion. Lo siguiente resume el estado al momento de redactar la guia.

| Tecnologia | Licencia | Requisitos clave | Uso comercial |
| --- | --- | --- | --- |
| FastAPI | MIT | Incluir aviso de copyright y licencia en redistribuciones. | Libre de royalties; permite modificaciones y distribucion comercial sin restricciones adicionales. |
| Uvicorn | BSD-3-Clause | Mantener avisos de copyright y no usar nombres de autores para promocion sin permiso. | Utilizable comercialmente sin tarifas; requiere conservar avisos. |
| Pydantic / Pydantic-Settings | MIT | Igual que FastAPI (MIT). | Compatible con soluciones a medida; basta con mantener avisos en distribuciones binarias. |
| httpx | BSD-3-Clause | Conserva avisos y renuncia de garantias. | Sin restricciones de uso comercial. |
| python-dotenv | BSD-3-Clause | Mismas obligaciones que BSD (avisos, no respaldo implicito). | Uso comercial permitido. |
| orjson | Apache-2.0 | Incluir copia de la licencia y avisos de cambios significativos. | Se puede usar comercialmente; obliga a conservar la licencia. |
| structlog | Apache-2.0 | Igual que orjson (avisos, no usar marcas registradas). | Libre para productos comerciales. |
| pytest / pytest-asyncio | MIT | Mantener avisos en redistribuciones. | Sin restricciones comerciales. |
| llama-cpp-python | MIT | Aplican clausulas MIT (avisos, renuncia de responsabilidad). | Permitido en soluciones comerciales siempre que se incluya la licencia si se redistribuye. |
| langchain / langchain-community | Apache-2.0 | Conservar licencia y archivo NOTICE si lo hay; documentar cambios. | Apto para SaaS o productos comercializados. |
| chromadb | Apache-2.0 | Idem Apache-2.0. | Uso comercial permitido. |
| sentence-transformers | Apache-2.0 | Verificar licencias de modelos especificos descargados. | Generalmente libre; revisar Terminos de modelos HuggingFace. |
| transformers | Apache-2.0 | Igual que arriba; revisar licencias de modelos concretos. | Libre, sujeto a licencia del modelo usado. |
| SQLAlchemy | MIT | Mantener avisos. | Sin restricciones comerciales. |
| asyncpg | Apache-2.0 | Conservar licencia/notices. | Permitido comercialmente. |
| Alembic | MIT | Avisos obligatorios. | Libre para SaaS/comercial. |
| redis (redis-py) | MIT | Avisos. | Uso comercial permitido. |
| Tenacity | Apache-2.0 | Avisos, no uso de marcas. | Libre de royalties; obligado a mantener licencia. |
| OpenTelemetry API/SDK | Apache-2.0 | Avisos y archivo NOTICE. | Integrable comercialmente sin restricciones. |
| Typer | MIT | Avisos. | Uso comercial permitido.

### Recomendaciones para comercializar soluciones a medida
- Mantener un archivo `THIRD_PARTY_NOTICES.md` con enlaces a las licencias incluidas.
- Automatizar auditorias (por ejemplo, `pip-licenses`) antes de cada release.
- Documentar modelos de lenguaje y datasets con sus propios terminos (algunos modelos GGUF derivan de pesos con licencias mas restrictivas).
- Si se empaqueta como SaaS, agregar las licencias en la documentacion publica o en la seccion "Terminos y condiciones" de la plataforma.
- Verificar export compliance si se distribuyen binarios con criptografia (aplica a ciertos modelos y dependencias).

