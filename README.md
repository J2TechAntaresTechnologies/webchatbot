<img src="docs/antares_technologies_srl_cover.jpeg" alt="Antares Technologies SRL — Cover">

# Chatbot Municipal Híbrido

Base del proyecto para un chatbot web municipal que combina respuestas fijas con generación vía LLM bajo guardrails.

## Mejoras recientes
- Portal con editor de Configuración por bot (temperature, top‑p, max tokens, pre‑prompts, menú de sugerencias) y editor dedicado de Reglas.
- Gestor de temas (light/dark + personalizados) persistidos en `localStorage` y aplicados en todas las vistas.
- API de settings: `/chatbots/{id}/settings` (GET/PUT) y reset `/chatbots/{id}/settings/reset` (POST) con persistencia en `chatbots/<id>/settings.json`.
- RAG con soporte JSONC (comentarios `//` y `/* */`) en `knowledge/faqs/municipal_faqs.json` y umbral configurable por bot (`rag_threshold`).
- Motor de reglas con coincidencia flexible k‑de‑n (min_matches) en reglas por defecto para reducir falsos positivos.
- Orquestador con pre‑prompts, respuestas genéricas opcionales cuando no hay match y canal MAR2/Free que va directo al LLM.

## Componentes previstos
- **Frontend web**: interfaz accesible con chat y streaming (prototipo estático disponible).
- **API Gateway (FastAPI)**: endpoints `/chat`, `/faq`, `/handoff`, rate limiting y autenticación.
- **Orquestador**: clasificación de intención, motor de respuestas fijas, RAG y LLM con moderación.
- **Adaptador LLM**: integración encapsulada con Llama.cpp u otros proveedores.
- **Knowledge base**: ingestión de FAQs y documentos municipales.
- **Infraestructura**: Docker, CI/CD, observabilidad.

## Estructura del repositorio
```
frontend/
chatbots/
modelos/
services/
  api/
  orchestrator/
  llm_adapter/
knowledge/
infrastructure/
tests/
docs/
```

- `services/api`: aplicación FastAPI y punto de entrada (`main.py`).
- `services/orchestrator`: motor de decisiones, clasificación de intents y conectores RAG/LLM.
- `services/llm_adapter`: stub del cliente LLM.
- `services/chatbots`: modelos y API de configuración por bot.
- `knowledge/faqs`: dataset JSON/JSONC para el RAG léxico de ejemplo (admite comentarios; el loader los elimina en runtime).
- `frontend`: portal estático y clientes que consumen `/chat/message` vía `fetch`.
- `chatbots/`: variantes de chatbots con metadatos y configuración (p. ej. `chatbots/municipal/config.json`).
- `modelos/`: carpeta compartida opcional para archivos `.gguf` accesibles por la aplicación.
- `docs`: arquitectura, roadmap y manuales.

## Estado actual
- Endpoint `/chat/message` expuesto a través de FastAPI y orquestador modular.
- Clasificador de intents heurístico con rutas a Reglas FAQ/Fallback (custom + default), RAG léxico y fallback (genérico opcional) o LLM.
- Base de conocimiento de ejemplo (`knowledge/faqs/municipal_faqs.json`) usada por el RAG (con soporte de comentarios JSONC).
- Tests unitarios cubren reglas, RAG, fallback y handoff; `./bin/python -m pytest` para ejecutar.
- Frontend con portal y variantes: `frontend/index.html` (Portal de Chatbots), `frontend/municipal.html` (Chatbot Municipal) y `frontend/mar2.html` (MAR2, conversación libre) con integración vía `fetch`.
- Portal incluye: editor de parámetros (guardar/leer vía API), editor de reglas, ayuda integrada y gestor de temas.

## Parámetros: Reglas y RAG (cómo funciona)
- Orden de decisión del orquestador: Reglas (FAQ/Fallback) → RAG → Genérico (si está habilitado y no hubo match) → LLM.
- Reglas
  - Dos orígenes posibles para trazabilidad: `faq` (respuestas oficiales) y `fallback` (saludos/ayuda/menú, smalltalks). Ambas cortan el flujo si matchean.
  - Coincidencia: match por subcadena en texto normalizado (minúsculas, sin tildes). El motor por defecto soporta reglas "suaves" k‑de‑n (min_matches) para reducir falsos positivos.
  - Personalización: desde el Portal se pueden agregar reglas propias (keywords, respuesta, origen, enabled). Las reglas propias se priorizan sobre las por defecto.
  - No existen “reglas RAG”. RAG es una etapa separada de recuperación en base de conocimiento.
- RAG
  - Toggle `features.use_rag`: activa/desactiva la búsqueda en `knowledge/faqs/municipal_faqs.json` cuando el intent del clasificador es `rag`.
  - `rag_threshold` [0–1]: umbral mínimo de similitud de coseno para aceptar la respuesta. Default 0.28; recomendado 0.20–0.40 según calidad de datos.
  - Si no supera el umbral, continúa el flujo (genérico/LLM).
  - Afinado: mejorar `tags` en el dataset y ajustar el umbral según recall/precisión deseados.


## Configuración por bot (settings)
- Persistencia: `chatbots/<id>/settings.json` (creado/actualizado por la API de settings y el Portal).
- Campos clave:
  - `generation`: `temperature`, `top_p`, `max_tokens`.
  - `features`: `use_rules`, `use_rag`, `enable_default_rules`, `use_generic_no_match` (este último muestra respuestas genéricas opcionales cuando no hay match).
  - `rag_threshold`: umbral RAG por bot.
  - `menu_suggestions`: lista de atajos (label + message) visibles en el cliente.
  - `pre_prompts`: instrucciones que se inyectan antes del mensaje del usuario.
  - `rules`: reglas personalizadas (enabled, keywords, response, source=faq|fallback).

Valores por defecto:
- Bot `municipal`: reglas y RAG activados, menú de sugerencias inicial y respuestas genéricas desactivadas.
- Bot `mar2` (modo libre): reglas y RAG desactivados por defecto; la conversación va directa al LLM.

## Instalación
1. Crear/activar entorno virtual (recomendado Python 3.10+). En este repositorio se incluye uno (`bin/python`).
2. Instalar dependencias base: `pip install -r requirements.txt` (aplica sólo las librerías mínimas).
3. Para ejecutar pruebas: `pip install -r requirements/dev.txt` y luego `python -m pytest` (o `make test`).
4. Extras opcionales (RAG/LLM): `pip install -r requirements/rag.txt`.
5. (Opcional NLP avanzado) Instalar spaCy en entorno separado: `pip install -r requirements-nlp.txt`.
   - Nota: FastAPI trae `fastapi-cli` que requiere `typer>=0.15`, mientras spaCy depende de `typer<0.10`. Para evitar conflictos, usar un virtualenv distinto o instalar `requirements-nlp.txt --no-deps` y fijar manualmente `typer` según la herramienta que se necesite.

Atajos con Make (equivalentes a los pasos anteriores):
- `make install-base` → instala dependencias mínimas (`requirements.txt`).
- `make install-dev` → instala base + herramientas de pruebas.
- `make install-rag` → instala extras para RAG/LLM.
- `make test` → ejecuta la suite de tests.

## Ejecución local
1. Levantar la API:
   ```bash
   uvicorn services.api.main:app --reload
   ```
2. Servir el frontend (opcional) en otro terminal:
   ```bash
   python -m http.server --directory frontend 5173
   ```
3. Abrir `http://localhost:5173` para ver el Portal y elegir una variante, o consumir la API en `http://localhost:8000/chat/message`.
   - Directos: `http://localhost:5173/municipal.html` (Chatbot Municipal) o `http://localhost:5173/mar2.html` (MAR2; envía `channel="mar2"`).
   - Si accedés desde otra máquina usando la IP pública (p. ej. `http://181.1.44.193:5173`), el frontend detecta automáticamente el host y consulta `:8000` en la misma IP. Para apuntar a otra ruta (reverse proxy/TLS), definí antes de `app.js` una variable global: `<script>window.WEBCHATBOT_API_BASE_URL="https://mi-dominio.com";</script>`.

Ejecución combinada (API + frontend) en una sola orden:
- `./start.sh` inicia ambos procesos (usa `tmux` si está instalado). Detener con `Ctrl+C` o cerrando la sesión de tmux.

Probar el endpoint vía cURL (sin frontend):
- Modo web (con reglas/FAQ/RAG):
  ```bash
  curl -sS -X POST \
    http://127.0.0.1:8000/chat/message \
    -H 'Content-Type: application/json' \
    -d '{"session_id":"web-local","message":"Necesito el horario de atención","channel":"web"}'
  ```
- Modo libre MAR2 (directo al LLM):
  ```bash
  curl -sS -X POST \
    http://127.0.0.1:8000/chat/message \
    -H 'Content-Type: application/json' \
    -d '{"session_id":"mar2-local","message":"Hola, ¿cómo estás?","channel":"mar2"}'
  ```

## Contrato del endpoint `/chat/message`
- **Request** (`POST`):
  - `session_id` (`str`, requerido) identificador único por conversación.
  - `message` (`str`, requerido) texto enviado por la persona usuaria.
  - `channel` (`str`, opcional) canal lógico; por defecto `"web"` según `ChatRequest` (`services/orchestrator/schema.py`).
- **Response**:
  - `session_id` (`str`) eco del identificador recibido.
  - `reply` (`str`) texto devuelto por el orquestador.
  - `source` (`str`) origen de la respuesta: `faq`, `rag`, `llm` o `fallback`.
  - `escalated` (`bool`) marca si el mensaje se deriva a un agente humano (true cuando el intent es `handoff`).

## API de configuración (`/chatbots`)
- GET `/chatbots/{id}/settings?channel=web`
- PUT `/chatbots/{id}/settings`
- POST `/chatbots/{id}/settings/reset?channel=web`

Ejemplos rápidos (curl):
- Obtener settings: `curl -sS "http://127.0.0.1:8000/chatbots/municipal/settings?channel=web" | jq .`
- Guardar cambios: `curl -sS -X PUT "http://127.0.0.1:8000/chatbots/municipal/settings" -H 'Content-Type: application/json' -d '{"features":{"use_rules":true,"use_rag":true},"rag_threshold":0.28}' | jq .`
- Resetear defaults: `curl -sS -X POST "http://127.0.0.1:8000/chatbots/municipal/settings/reset?channel=web" | jq .`

## Acceso externo (sin DNS)
Para hacer una prueba y permitir acceso desde fuera de tu red, sin registrar un dominio, tenés varias opciones. Elegí la que mejor se ajuste a tu entorno:

- Túnel rápido (recomendado para demos seguras con TLS):
  - Cloudflare Quick Tunnels: `cloudflared tunnel --url http://localhost:8000` y, en otra terminal, `cloudflared tunnel --url http://localhost:5173`. Obtendrás URLs públicas aleatorias `https://*.trycloudflare.com` con HTTPS.
  - ngrok: `ngrok http 8000` y `ngrok http 5173` generan URLs `https://*.ngrok.io` (requiere instalar `ngrok` y, según plan, autenticación).
  - localtunnel: `npx localtunnel --port 5173` y `--port 8000` crean subdominios temporales.
  - Ajustar CORS si usás un dominio público: exportá `WEBCHATBOT_ALLOWED_ORIGINS` antes de levantar la API, por ejemplo:
    ```bash
    export WEBCHATBOT_ALLOWED_ORIGINS="https://xxxx.trycloudflare.com,https://yyyy.trycloudflare.com"
    uvicorn services.api.main:app --host 0.0.0.0 --port 8000
    ```
    Nota: `*` funciona para pruebas rápidas pero no es recomendable en producción.
  - Si el frontend apunta a un dominio distinto al de la API, agregá en tus páginas HTML antes de `app.js/app_mar2.js`:
    ```html
    <script>window.WEBCHATBOT_API_BASE_URL="https://tu-url-publica-de-api";</script>
    ```

- Reenvío de puertos con SSH (si contás con un servidor accesible):
  - API: `ssh -N -R 0.0.0.0:18000:localhost:8000 usuario@servidor`.
  - Frontend: `ssh -N -R 0.0.0.0:15173:localhost:5173 usuario@servidor`.
  - Accedé desde fuera en `http://IP_DEL_SERVIDOR:18000` y `http://IP_DEL_SERVIDOR:15173`.
  - Asegurate de tener `GatewayPorts yes` en el servidor SSH y de abrir los puertos en su firewall.

- Redirección de puertos en tu router (NAT) — útil si tenés IP pública y control del router:
  1. Exponé `8000` (API) y `5173` (frontend) hacia la IP local de tu máquina.
  2. Abrí los puertos en el firewall local (ej. UFW): `sudo ufw allow 8000,5173/tcp`.
  3. Levantá los servicios escuchando en todas las interfaces:
     ```bash
     uvicorn services.api.main:app --host 0.0.0.0 --port 8000
     python -m http.server --directory frontend 5173 --bind 0.0.0.0
     ```
  4. Para CORS, definí `WEBCHATBOT_ALLOWED_ORIGINS` con la(s) URL(s) que usarán desde fuera (por ejemplo `http://TU_IP_PUBLICA:5173`).

Sugerencias de seguridad (incluso en pruebas):
- Preferí túneles con HTTPS (cloudflared/ngrok) en lugar de abrir puertos a Internet.
- No uses `WEBCHATBOT_ALLOWED_ORIGINS="*"` fuera de pruebas rápidas.
- Considerá habilitar `ufw` y registrar accesos (reverse proxy con logs y rate-limiting si la prueba se extiende).

## Variables de entorno útiles
- `WEBCHATBOT_ALLOWED_ORIGINS`: lista de orígenes permitidos para CORS (coma‑separados o `*`).
- `window.WEBCHATBOT_API_BASE_URL` (frontend): define la URL base de la API cuando frontend y backend no comparten host/puerto.
- LLM: `LLM_MODEL_PATH`, `LLM_MAX_TOKENS`, `LLM_TEMPERATURE`, `LLM_TOP_P`, `LLM_CONTEXT_WINDOW`.

## Pruebas
1. Instalar dependencias de desarrollo: `make install-dev` (incluye `pytest` y `pytest-asyncio`).
2. Ejecutar la suite: `make test` o `./bin/python -m pytest` desde la raíz del repositorio.
3. Si preferís activar el entorno previo (`source bin/activate`), `pytest` quedará disponible en el `PATH`.
4. Añadir nuevos casos en `tests/unit/` para validar regresiones cada vez que se modifique el orquestador o la API.

Tip (sin activar el venv): `PYTHONPATH=. ./bin/pytest -q` también ejecuta la suite respetando los imports del proyecto.

## Configurar un LLM local
1. Instalar dependencias avanzadas: `make install-rag` (incluye `llama-cpp-python`).
2. Activa el entorno virtual con `source bin/activate`; el script `scripts/export_webchatbot_env.sh` se ejecuta automáticamente y exporta:
   - `WEBCHATBOT_PROJECT_ROOT` y añade el repo al `PYTHONPATH`.
   - `WEBCHATBOT_DEFAULT_LLM_MODEL_PATH` y `LLM_MODEL_PATH`, que por defecto apuntan a `/home/jim/.cache/llama.cpp/ggml-org_gemma-3-1b-it-GGUF_gemma-3-1b-it-Q4_K_M.gguf`.
3. Verificá que el archivo `.gguf` exista y que la versión de `llama-cpp-python` soporte la arquitectura (Gemma 3 requiere versiones recientes). Si preferís otro modelo, exportá previamente `WEBCHATBOT_DEFAULT_LLM_MODEL_PATH=/ruta/a/tu_modelo.gguf` o `LLM_MODEL_PATH=/ruta/custom.gguf` antes de activar el entorno.
4. Opcional: ajustar hiperparámetros mediante variables de entorno (`LLM_MAX_TOKENS`, `LLM_TEMPERATURE`, `LLM_TOP_P`, `LLM_CONTEXT_WINDOW`).
5. Si tras iniciar la API (`uvicorn services.api.main:app --reload`) el modelo falla al cargar, el orquestador regresará al mensaje placeholder; revisá los logs y la compatibilidad del binario.

## Base de conocimiento (FAQs)
- Dataset: `knowledge/faqs/municipal_faqs.json` (admite comentarios JSONC: `//` y `/* ... */`).
- Guías: `knowledge/README.md` y `knowledge/faqs/municipal_faqs.EXPLAIN.md` (cómo editar y buenas prácticas).
- Mejores resultados con preguntas concisas, respuestas claras y `tags` en minúscula que reflejen conceptos clave.

## Diagnóstico del host
- Ejecutá `./bin/python scripts/check_host_readiness.py` para medir recursos, dependencias, puertos y firewall antes de exponer el proyecto públicamente.
- Agregá `--skip-public-ip` si estás en una red sin salida directa a Internet o preferís evitar consultas externas.

## Próximos pasos sugeridos
Revisá `docs/roadmap.md` para un plan con los próximos 10 hitos técnicos.

## Documentación relacionada
- `docs/architecture.md`: visión técnica y capas del sistema.
- `docs/roadmap.md`: backlog priorizado para los próximos sprints.
- `docs/manual_aprendizaje.md`: guía de aprendizaje, extensiones y buenas prácticas para modificar el proyecto.
- `docs/operacion_configuracion_chatbots.md`: operación, configuración de chatbots y gestión de prompts.
- `README_ALTERNATIVO.txt`: guía rápida específica para la variante MAR2 (modo libre) con ejemplos de uso por CLI y navegador.
 - `chatbots/README.md`: guía para agregar nuevas variantes de chatbots.
 - `docs/rules_vs_rag.md`: diferencias, cuándo usar reglas vs RAG.
 - `docs/visualizacion.md`: ideas de visualización y monitoreo.

## Guías in‑code (referencia rápida)
- `services/orchestrator/intent_classifier.py`: uso, parametrización, impacto y presets de intents.
- `services/orchestrator/service.py`: flujo Reglas → RAG → Genérico (si habilitado) → LLM, pre_prompts, toggles y puntos de extensión.
- `services/orchestrator/rule_engine.py`: definición de reglas, matching y orden.
- `services/orchestrator/rag.py`: RAG ligero, threshold y dataset JSON/JSONC.
- `services/chatbots/models.py`: esquema de settings por bot e IO `chatbots/<id>/settings.json` (incluye reglas custom, toggles y respuestas genéricas).
- `services/chatbots/router.py`: API de settings (GET/PUT/POST reset) con ejemplos `curl`.
- `services/orchestrator/router.py`: contrato `POST /chat/message` y ejemplo.
- `services/llm_adapter/client.py`: cliente LLM, variables de entorno y logging.
- `services/llm_adapter/settings.py`: variables soportadas del LLM y fuentes (.env/env).
- `services/api/main.py`: CORS, routers habilitados y ejecución local.
- `frontend/portal.js`: endpoints de configuración, `API_BASE_URL` y consejos.
- `frontend/app.js`: cliente Municipal (channel "web").
- `frontend/app_mar2.js`: cliente MAR2 (modo libre).
<p align="center">
  <img src="docs/antares_technologies_srl_logo.jpeg" alt="Antares Technologies SRL — Logo">
</p>
