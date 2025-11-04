README alternativo — Ejecutar el “otro” chatbot (MAR2)

Este proyecto trae un portal y dos variantes de frontend:
- Portal: frontend/index.html (selección de chatbot)
- Chatbot Municipal: frontend/municipal.html (menú guiado)
- MAR2 (modo libre): frontend/mar2.html

MAR2 usa el mismo backend FastAPI pero envía channel="mar2" para saltar reglas y conversar libremente con el LLM.

REQUISITOS BÁSICOS
- Python 3.10+
- Dependencias mínimas instaladas: pip install -r requirements.txt (o make install-base)

1) Iniciar la API (FastAPI)
---------------------------------
En una terminal, desde la raíz del repo:

  uvicorn services.api.main:app --reload

La API queda en http://127.0.0.1:8000 (o 0.0.0.0 si lo exponés con --host 0.0.0.0).

2) Probar MAR2 por CLI (sin frontend)
-------------------------------------
En otra terminal podés enviar mensajes directamente al endpoint con channel="mar2":

  curl -sS -X POST \
    http://127.0.0.1:8000/chat/message \
    -H 'Content-Type: application/json' \
    -d '{"session_id":"mar2-local","message":"Hola, ¿cómo estás?","channel":"mar2"}' | jq .

Respuesta esperada (ejemplo):
  {
    "session_id": "mar2-local",
    "reply": "...texto generado o placeholder...",
    "source": "llm",
    "escalated": false
  }

3) Usar el frontend MAR2 en navegador
-------------------------------------
Serví la carpeta frontend en puerto 5173 y abrí el portal o mar2.html:

  python -m http.server --directory frontend 5173

Luego en el navegador:
  http://localhost:5173  (Portal) o http://localhost:5173/mar2.html

El cliente web detecta la API en :8000 de la misma máquina. Si querés apuntar a otro dominio/puerto (por reverse proxy o TLS), agregá antes de app_mar2.js en mar2.html una variable global:

  <script>window.WEBCHATBOT_API_BASE_URL="https://mi-dominio.com";</script>

4) Opcional: activar LLM local
------------------------------
Si tenés un modelo .gguf y llama-cpp-python instalado, MAR2 generará respuestas reales del LLM. Sugerido:

  make install-rag
  source bin/activate

Al activar, scripts/export_webchatbot_env.sh exporta LLM_MODEL_PATH por defecto. Para usar otra ruta:

  export WEBCHATBOT_DEFAULT_LLM_MODEL_PATH="/ruta/a/tu_modelo.gguf"
  # o directamente
  export LLM_MODEL_PATH="/ruta/a/tu_modelo.gguf"

Volvé a iniciar la API con uvicorn. Si el modelo no carga, el orquestador responde con un placeholder.

5) Ejecución combinada (API + frontend)
---------------------------------------
Si tenés tmux instalado, podés levantar ambos con:

  ./start.sh

Abrí después:
  http://localhost:5173/mar2.html

Notas útiles
- Endpoint de chat: POST /chat/message
- Campos: session_id (str), message (str), channel (str opcional). Para MAR2 usar channel="mar2".
- Si exponés el frontend por IP pública, el cliente intentará hablar con :8000 en la misma IP. Ajustá WEBCHATBOT_API_BASE_URL si necesitás otra ruta.
