# Guía de visualización (frontend)

Este documento indica dónde modificar los aspectos visuales del chat (tamaño, colores, tipografía, burbujas, botones) y del portal. Incluye referencias a archivos y líneas para ubicar rápido cada ajuste.

## Estructura de páginas

- Cliente Municipal: `frontend/municipal.html:10`
  - Contenedor principal: `<main class="chat-container">` con `#chat-log` y formulario.
- Cliente MAR2: `frontend/mar2.html:10`
  - Misma estructura base que municipal, más un resumen de parámetros (`#config-summary`).
- Portal (selector de bots y modal de parámetros): `frontend/index.html:10`
  - Topbar con selector de temas y modal con formularios para settings de bots.

## Tamaños y layout del chat

- Contenedor general (ancho, padding, radios, sombra)
  - `frontend/styles.css:56` → `.chat-container { width: min(640px, 95vw); padding: 1.75rem; border-radius: 16px; … }`
  - Cambiar ancho: usar `min(800px, 95vw)` o similar.
- Área de conversación (alto mínimo/máximo, scroll)
  - `frontend/styles.css:76` → `.chat-log { min-height: 280px; max-height: 420px; overflow-y: auto; … }`
  - Para pantallas altas, considerar `max-height: 60vh;`.
- Burbujas (ancho relativo, espaciado, saltos de línea)
  - `frontend/styles.css:92` → `.message { max-width: 80%; white-space: pre-wrap; … }`
  - Aumentar `max-width` para burbujas más anchas; `white-space: pre-wrap` preserva saltos si el texto contiene `\n`.

## Colores y tipografía

- Variables globales (tema base)
  - `frontend/styles.css:1` → `:root { --accent, --accent-strong, --surface, --surface-bright, --text-primary, --text-secondary, … }`
  - Cambiar aquí afecta todo el sitio por defecto.
- Gestión de temas (localStorage + aplicación dinámica)
  - `frontend/portal.js:3` (gestor de temas) y `frontend/app.js:1` (aplicar tema activo en cliente municipal).
  - Claves: `webchatbot_themes` y `webchatbot_active_theme`.
  - Modal de temas (Portal): `frontend/index.html:62` y lógica en `frontend/portal.js:109`.
  - Variables soportadas también incluyen tipografía: `--font-family`, `--font-size` (`frontend/portal.js:7`).

## Estilos de burbujas, inputs y botones

- Burbujas del usuario y bot
  - Usuario: `frontend/styles.css:102` → `.message.user { background: linear-gradient(…); color: #07101f; … }`
  - Bot: `frontend/styles.css:110` → `.message.bot { background: var(--surface-bright); border: 1px solid … }`
- Entradas de texto
  - `frontend/styles.css:132` → `input { border, border-radius, padding, background, color, focus }`
- Botones
  - Base: `frontend/styles.css:149` → `button { background: linear-gradient(…); border-radius; padding; … }`
  - Hover/deshabilitado: `frontend/styles.css:160`, `frontend/styles.css:166`.
  - Enlaces estilo botón (Portal): `frontend/styles.css:207` → `.btn-link { … }`
  - Botón flotante “Salir”: `frontend/styles.css:297` → `.fab-exit { position: fixed; … }`
- Chips/sugerencias y resumen de config
  - Chips: `frontend/styles.css:286` → `.suggestion-chip { … }`
  - Resumen: `frontend/styles.css:177` → `.config-summary { … }`

## Saltos de línea en respuestas del bot

- El frontend reemplaza `\n` por `<br>` de forma segura para que el menú y otros textos se muestren en varias líneas.
  - Cliente municipal: `frontend/app.js:57` → función `toSafeHtml()` + uso en `appendMessage()` (`frontend/app.js:69`).
  - MAR2: `frontend/app_mar2.js:59` (definición `toSafeHtml`) y `frontend/app_mar2.js:70` (uso en `appendMessage`).
- Además, `.message { white-space: pre-wrap; }` (`frontend/styles.css:92`) ayuda a preservar el formato si se insertan `\n` literales.

## Portal y modal de parámetros

- Topbar y selector de temas: `frontend/index.html:11` (clase `.topbar`), estilos en `frontend/styles.css:29`.
- Modal de parámetros (ancho/estilos)
  - Marcado: `frontend/index.html:22` (backdrop) y `frontend/index.html:24` (contenedor `.modal`).
  - Estilos: `frontend/styles.css:221` (backdrop), `frontend/styles.css:237` (cuadro del modal), `frontend/styles.css:253` (fieldset), `frontend/styles.css:273` (acciones).

## Imágenes, fondos y efectos

- Fondo principal del body: `frontend/styles.css:17` (`--bg-main` radial-gradient). Se puede cambiar a un color sólido o imagen.
- Sombras y blur del contenedor: `frontend/styles.css:61` (`backdrop-filter`, `box-shadow`).

## Dónde tocar para…

- “Hacer más ancho el chat”: `frontend/styles.css:56` → subir el valor en `width: min(…)`.
- “Hacer más alto el área de mensajes”: `frontend/styles.css:76` → subir `max-height` o usar `vh`.
- “Cambiar colores y tipografía”: `frontend/styles.css:1` y/o desde el Portal (temas) `frontend/portal.js:109`.
- “Mostrar saltos de línea del backend”: ya aplicado vía `<br>` (ver `frontend/app.js:57`).
- “Cambiar estilo de botones”: `frontend/styles.css:149` (global) y `frontend/styles.css:207` (enlaces tipo botón).

## Notas

- El cliente usa `textContent` para mensajes del usuario y `innerHTML` escapado para el bot con `<br>`. No se renderiza HTML arbitrario para evitar XSS.
- Si agregás nuevos componentes visuales, mantené la coherencia con las variables de `:root` y el sistema de temas del Portal.
