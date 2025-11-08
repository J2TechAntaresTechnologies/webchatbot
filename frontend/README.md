# Frontend

 Semilla ligera del cliente web y portal de selección de chatbots. Incluye:
- `index.html` (Portal de Chatbots: lista variantes disponibles).
- `municipal.html` (Chatbot Municipal, con saludo inicial y pista de menú con "ayuda").
- `mar2.html` (MAR2, tema oscuro y conversación libre sin prompt inicial ni menús).
  - Muestra, sobre el cuadro de chat, los parámetros activos (temperature, top‑p, max tokens) y los pre‑prompts configurados antes de entrar.

## Uso rápido
1. Servir la carpeta con cualquier servidor estático (`python -m http.server --directory frontend 5173`).
2. Ejecutar la API (`uvicorn services.api.main:app --reload`).
 3. Abrir:
   - `http://localhost:5173` para ver el Portal y elegir un chatbot.
   - `http://localhost:5173/municipal.html` para ir directo al Chatbot Municipal.
   - `http://localhost:5173/mar2.html` para MAR2 (modo libre).

Notas sobre la URL de la API
- Por defecto el cliente intenta contactar `:8000` en el mismo host desde el que servís el frontend (ej.: `http://127.0.0.1:8000`).
- Si necesitás apuntar a otra ruta/dominio (reverse proxy, TLS), definí antes del `app.js`/`app_mar2.js` una variable global:
  ```html
  <script>window.WEBCHATBOT_API_BASE_URL="https://mi-dominio.com";</script>
  ```

Acceso externo (sin DNS)
- Para demos públicas sin registrar un dominio, podés usar túneles:
  - Cloudflare Quick Tunnels: `cloudflared tunnel --url http://localhost:5173` (frontend) y `--url http://localhost:8000` (API).
  - ngrok: `ngrok http 5173` y `ngrok http 8000`.
  - localtunnel: `npx localtunnel --port 5173` y `--port 8000`.
- Si frontend y API quedan en hosts diferentes, definí `window.WEBCHATBOT_API_BASE_URL` en las páginas HTML del cliente para apuntar a la URL pública de la API.
- En la API, ajustá CORS con `WEBCHATBOT_ALLOWED_ORIGINS` para incluir las URLs públicas.

## Temas (colores)
- En el Portal (`index.html`) hay un botón "Configuración" arriba a la derecha y un selector rápido de tema.
- Podés:
  - Aplicar temas guardados desde el selector "Tema" (cambia el estilo en el acto).
  - Crear/editar un tema (accent, superficies y colores de texto) y Guardarlo.
  - Actualizar un tema existente o Eliminarlo. El tema `default` es el único que no puede borrarse ni sobrescribirse.
- Persistencia:
  - Los temas se guardan en `localStorage` del navegador bajo la clave `webchatbot_themes` y el tema activo en `webchatbot_active_theme`.
  - El tema activo se aplica automáticamente en todas las vistas (`index.html`, `municipal.html`, `mar2.html`).

## Parámetros visibles en MAR2
- La pantalla `mar2.html` lee la configuración del bot MAR2 desde la API y muestra un resumen arriba del cuadro de chat:
  - Generation: `temperature`, `top_p`, `max_tokens`.
  - Pre‑prompts: lista rápida como chips.
- Para cambiar estos valores, usá el botón Configuración en el Portal y editá la variante MAR2.

## Próximos pasos
1. Migrar a un bundler moderno (Vite/React) manteniendo accesibilidad y soporte móvil.
2. Configurar cliente API con streaming (SSE/WebSocket) y estados de carga.
3. Integrar autenticación municipal y gestión de sesiones.
4. Añadir componentes reutilizables de diseño municipal y pruebas de usabilidad.

Más detalles sobre arquitectura de frontend y lineamientos de diseño en `docs/manual_aprendizaje.md`.

## Parámetros de Reglas y RAG (Portal)
- Reglas (FAQ/Fallback): respuestas fijas por keywords. En el Portal, el modal de Parámetros muestra un resumen y abre un editor dedicado (“Editar reglas…”). No existen “reglas RAG”; RAG es otra etapa distinta.
- Orden de decisión (backend): Reglas → RAG → Genérico (si está ON) → LLM.
- RAG
  - Toggle: “Usar RAG” habilita la búsqueda en `knowledge/faqs/municipal_faqs.json` cuando el intent es `rag`.
  - `RAG threshold` (0–1): umbral mínimo de similitud para aceptar la respuesta. 0.20–0.40 recomendado. Default 0.28.
  - Sugerencias: bajar el umbral sube recall pero puede traer respuestas “parecidas”; subirlo aumenta precisión pero responde menos por RAG.

## Accesibilidad y scroll en modales
- Los modales de Configuración, Reglas y Ayuda limitan altura y permiten scroll interno para evitar desbordes en pantallas pequeñas.
- Clases involucradas: `.modal` (max-height y overflow), `.settings-form` y `.help-body` (scroll interno), con scrollbar coherente al estilo del chat.
