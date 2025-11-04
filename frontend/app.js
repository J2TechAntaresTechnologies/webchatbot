// --- Tema activo desde localStorage ---
(function applyActiveTheme() {
  try {
    const THEME_KEY = 'webchatbot_themes';
    const ACTIVE_KEY = 'webchatbot_active_theme';
    const VARS = ['--accent','--accent-strong','--surface','--surface-bright','--text-primary','--text-secondary'];
    const saved = JSON.parse(localStorage.getItem(THEME_KEY) || '[]');
    const themes = Array.isArray(saved) ? saved : [];
    function getDefaultTheme() {
      const vars = {};
      const cs = getComputedStyle(document.documentElement);
      for (const k of VARS) vars[k] = cs.getPropertyValue(k).trim();
      return { name: 'default', vars };
    }
    const all = [{ name: 'default', vars: getDefaultTheme().vars }, ...themes.filter(t => t && t.name && t.name !== 'default')];
    const active = localStorage.getItem(ACTIVE_KEY) || 'default';
    const theme = all.find(t => t.name === active) || all[0];
    const root = document.documentElement;
    for (const k of VARS) {
      const v = theme.vars[k];
      if (v) root.style.setProperty(k, v); else root.style.removeProperty(k);
    }
  } catch {}
})();

const generateSessionId = () => {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  const randomSuffix = Math.random().toString(16).slice(2);
  return `session-${Date.now()}-${randomSuffix}`;
};

const sessionId = generateSessionId();
const BOT_ID = "municipal";
let currentController = null;
const chatLog = document.getElementById("chat-log");
const form = document.getElementById("chat-form");
const input = document.getElementById("message");

const API_BASE_URL = (() => {
  const override = typeof window !== "undefined" ? window.WEBCHATBOT_API_BASE_URL : null;
  if (typeof override === "string" && override.trim() !== "") {
    return override.replace(/\/$/, "");
  }

  const { protocol, hostname, port } = window.location;
  if (port === "5173" || hostname === "0.0.0.0") {
    const targetHost = ["localhost", "127.0.0.1", "0.0.0.0"].includes(hostname)
      ? "127.0.0.1"
      : hostname;
    return `${protocol}//${targetHost}:8000`;
  }
  return "";
})();

const appendMessage = (role, text) => {
  const bubble = document.createElement("article");
  bubble.classList.add("message", role);
  bubble.textContent = text;
  chatLog.appendChild(bubble);
  chatLog.scrollTop = chatLog.scrollHeight;
};

const setSubmitting = (isSubmitting) => {
  form.querySelector("button").disabled = isSubmitting;
  input.disabled = isSubmitting;
};

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) {
    return;
  }

  appendMessage("user", message);
  input.value = "";
  setSubmitting(true);

  try {
    currentController = new AbortController();
    const response = await fetch(`${API_BASE_URL}/chat/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: currentController.signal,
      body: JSON.stringify({
        session_id: sessionId,
        message,
        channel: "web",
        bot_id: BOT_ID,
      }),
    });

    if (!response.ok) {
      throw new Error(`Error HTTP ${response.status}`);
    }

    const payload = await response.json();
    appendMessage("bot", payload.reply ?? "Sin respuesta");
  } catch (error) {
    console.error(error);
    appendMessage(
      "bot",
      "No pudimos contactar al servidor. Verificá que la API esté corriendo en http://127.0.0.1:8000."
    );
  } finally {
    currentController = null;
    setSubmitting(false);
    input.focus();
  }
});

appendMessage(
  "bot",
  "¡Hola! Soy el asistente municipal. Escribí tu consulta o pedí 'ayuda' para ver las opciones disponibles."
);

// Sugerencias de menú desde configuración del servidor
(async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/chatbots/${BOT_ID}/settings?channel=web`, { cache: "no-cache" });
    if (!res.ok) return;
    const settings = await res.json();
    const items = Array.isArray(settings.menu_suggestions) ? settings.menu_suggestions : [];
    if (items.length === 0) return;
    const container = document.createElement("div");
    container.id = "suggestions";
    for (const it of items) {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "suggestion-chip";
      chip.textContent = it.label || it.message;
      chip.addEventListener("click", () => {
        input.value = it.message || "";
        input.focus();
      });
      container.appendChild(chip);
    }
    const formEl = document.getElementById("chat-form");
    formEl.parentNode.insertBefore(container, formEl);
  } catch (e) {
    // silencioso
  }
})();

// Botón Salir: aborta solicitud en curso y vuelve al portal (fail-safe si no existe en el HTML)
function ensureExitButton() {
  let exitBtn = document.getElementById("exit-btn");
  if (!exitBtn) {
    exitBtn = document.createElement("button");
    exitBtn.id = "exit-btn";
    exitBtn.type = "button";
    exitBtn.className = "fab-exit";
    exitBtn.textContent = "Salir";
    document.body.appendChild(exitBtn);
  }
  exitBtn.addEventListener("click", () => {
    try {
      if (currentController) currentController.abort();
    } catch {}
    window.location.href = "index.html";
  });
}

ensureExitButton();

// ================================================================
// Guía rápida (Cliente Municipal web)
// ================================================================
//
// Comportamiento
// --------------
// - Envía mensajes a POST /chat/message con channel="web" y bot_id="municipal".
// - Muestra chips de sugerencias desde /chatbots/municipal/settings (menu_suggestions).
// - No guarda historial (stateless en cliente); la API responde de inmediato.
//
// API_BASE_URL
// ------------
// - Autodetecta :8000 si se sirve el frontend en :5173. Sobrescribible con
//   window.WEBCHATBOT_API_BASE_URL.
//
// Consejos
// --------
// - El orquestador aplicará Reglas/FAQ y RAG antes del LLM. Ajustar toggles
//   y pre_prompts desde el Portal para modificar el comportamiento.
