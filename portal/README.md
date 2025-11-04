# Portal de Chatbots — Guía de Estructura y Operación

Este documento describe la nueva estructura “portal de chatbots”, los cambios introducidos, y un manual práctico para configurar, parametrizar, ejecutar y extender el proyecto con múltiples variantes de chatbots sobre la misma base.

## Objetivo
- Usar una sola base de código para varias variantes de chatbots (p. ej., Municipal guiado, MAR2 libre, etc.).
- Ofrecer una landing única (Portal) donde elegir qué chatbot abrir.
- Centralizar recursos compartidos (modelos, conocimiento) y permitir configuración por variante.

## Estructura del proyecto (resumen)
frontend/
  index.html           # Portal (landing) con selector de variantes
  chatbots.json        # Registro visible por el Portal (lista de variantes)
  portal.js            # Lógica de render del Portal
  municipal.html       # Cliente de la variante “Municipal” (guiada)
  mar2.html            # Cliente de la variante “MAR2” (modo libre)
  app.js, app_mar2.js  # Lógicas de cliente por variante
chatbots/
  municipal/config.json  # Metadatos/params de la variante
  mar2/config.json       # Metadatos/params de la variante
modelos/
  ... .gguf            # Modelos LLM locales compartidos
services/
  api/main.py          # API FastAPI
  orchestrator/...     # Orquestador (reglas, RAG, LLM)
knowledge/
  faqs/...             # Datos de ejemplo para RAG léxico
scripts/
  export_webchatbot_env.sh  # Variables de entorno y detección de modelos
  check_host_readiness.py   # Diagnóstico del host

## Cambios clave introducidos
- Portal como landing: frontend/index.html ahora muestra un menú con tarjetas para cada chatbot registrado en frontend/chatbots.json usando frontend/portal.js.
- Separación de variantes existentes:
  - frontend/municipal.html (antes index.html) mantiene el flujo guiado del “Chatbot Municipal”.
  - frontend/mar2.html sigue siendo la variante de conversación libre.
- Registro de chatbots: chatbots/<id>/config.json define metadatos por variante (id, nombre, descripción, canal sugerido y página frontend). El Portal consume frontend/chatbots.json para listar opciones.
- Modelos locales compartidos: carpeta modelos/ en la raíz. El script scripts/export_webchatbot_env.sh prioriza el primer .gguf encontrado allí como default si no hay LLM_MODEL_PATH definido.

## Parámetros y configuración
- Variables de entorno (leer en services/llm_adapter/settings.py y scripts/export_webchatbot_env.sh):
  - LLM_MODEL_PATH: ruta absoluta al modelo .gguf a usar.
  - WEBCHATBOT_DEFAULT_LLM_MODEL_PATH: valor por defecto si no se define LLM_MODEL_PATH. Ahora puede tomarse automáticamente del directorio modelos/.
  - LLM_MAX_TOKENS, LLM_TEMPERATURE, LLM_TOP_P, LLM_CONTEXT_WINDOW: hiperparámetros del generador LLM.
 - WEBCHATBOT_API_BASE_URL (frontend): URL base de la API cuando no se usa la detección automática :8000 en el mismo host. Definirla en la página HTML antes de cargar el script del cliente.
- Metadatos por chatbot: chatbots/<id>/config.json
  {
    "id": "municipal",
    "name": "Chatbot Municipal",
    "description": "Versión guiada con reglas/FAQ y RAG básico.",
    "channel": "web",
    "frontend_page": "municipal.html"
  }
 - channel: sugiere el canal lógico que enviará el frontend al backend (en app.js/app_mar2.js). Actualmente:
    - web: flujo guiado (reglas/FAQ, RAG y fallback LLM).
    - mar2 o free: va directo al LLM (con placeholder si no hay modelo).

## Ejecución
1. Iniciar API: uvicorn services.api.main:app --reload
2. Servir frontend: python -m http.server --directory frontend 5173
3. Abrir Portal: http://localhost:5173 y elegir una variante. Directos:
   - Municipal: http://localhost:5173/municipal.html
 - MAR2: http://localhost:5173/mar2.html
4. Combinado: ./start.sh levanta API y frontend en paralelo (usa tmux si está disponible).

## Cómo agregar un nuevo chatbot (paso a paso)
1) Crear metadatos de la variante
   - Directorio: `chatbots/<id>/`
   - Archivo: `chatbots/<id>/config.json` con, al menos:
     {
       "id": "<id>",
       "name": "<Nombre visible>",
       "description": "<Breve descripción>",
       "channel": "web|mar2|free|<otro>",
       "frontend_page": "<id>.html"
     }
2) Crear el cliente web de la variante
   - Página: `frontend/<id>.html` (podés duplicar `frontend/municipal.html` o `frontend/mar2.html`).
   - Script: reutilizar `frontend/app.js` (canal "web") o `frontend/app_mar2.js` (canal "mar2"). Para un canal nuevo, copiá uno de esos como base y ajustá el valor del campo `channel` en el body de la request `POST /chat/message`.
3) Agregar un nuevo acceso directo al menú principal (Portal)
   - Editar `frontend/chatbots.json` y añadir un objeto con `id`, `name`, `description` y `frontend_page`.
   - Guardar y recargar el Portal: aparecerá automáticamente una tarjeta con botón “Abrir”.
4) Apuntar dependencias comunes del sistema
   - Modelo LLM: colocar `.gguf` en `modelos/` o exportar `LLM_MODEL_PATH` hacia tu ruta preferida antes de iniciar la API.
   - Conocimiento RAG: agregar/actualizar archivos en `knowledge/` (por ejemplo `knowledge/faqs/*.json`).
5) Pruebas y verificación
   - Ejecutar `./bin/python -m pytest` para confirmar que no hubo regresiones.
   - Probar desde el navegador y/o con `curl` contra `POST /chat/message`.

## Extender el backend por variante (opcional)
El orquestador interpreta `channel` y hoy soporta:
- `mar2`/`free` → respuesta directa del LLM.
- `web` (u otro) → reglas/FAQ, RAG y fallback LLM.

Si tu variante necesita comportamiento diferente (reglas o RAG propios):
1) Definí un canal nuevo en tu cliente (`channel: "mi_variante"`).
2) En `services/orchestrator/service.py`, dentro de `ChatOrchestrator.respond()`, ramificá por `request.channel` y aplicá la lógica específica (p. ej., otra colección de reglas o un `RagResponderProtocol` distinto).
3) Añadí pruebas unitarias que envíen el canal nuevo y validen la ruta de respuesta.

Sugerencias:
- Para reglas por variante, instanciá `RuleBasedResponder` con una lista diferente según el canal.
- Para RAG por variante, creá un loader de entradas alternativo y adjuntalo con `attach_rag(...)` en el arranque.

## Parametrización del frontend y API base
- Detección automática: si el frontend corre en `:5173`, se consulta la API en `:8000` del mismo host.
- Override manual: en la página HTML, antes del script del cliente, definir:
  <script>window.WEBCHATBOT_API_BASE_URL = "https://mi-dominio.com";</script>
- Accesibilidad y estilos: el Portal reutiliza `frontend/styles.css`. Podés agregar clases si necesitás un look and feel distinto para tu tarjeta.

## Comandos útiles
- Instalar dependencias: `make install-base`, `make install-dev`, `make install-rag`.
- Ejecutar tests: `make test` o `./bin/python -m pytest`.
- Diagnóstico de entorno: `./bin/python scripts/check_host_readiness.py` (agregá `--skip-public-ip` si no hay salida a Internet).
- Arranque combinado: `./start.sh` (usa tmux cuando está instalado).

## Buenas prácticas
- Mantener `chatbots/<id>/config.json` como fuente de metadatos por variante.
- Centralizar modelos `.gguf` en `modelos/` para facilitar el uso y la detección automática.
- Versionar cambios de reglas/datos en `knowledge/` y cubrirlos con tests.
- Revisar CORS/seguridad en `services/api/main.py` al exponer fuera de localhost.

## FAQ
- ¿El Portal puede leer el registro desde la API?
  - Sí, se puede agregar un endpoint `GET /chatbots` que sirva el contenido de `frontend/chatbots.json` o `chatbots/<id>/config.json`. Hoy el Portal usa un JSON estático por simplicidad.
