// MAR2 - modo libre sin prompt ni menú

// --- Tema activo desde localStorage ---
// Aplica el tema activo leyendo variables de localStorage y setea CSS variables
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

// Identificador único de sesión para correlacionar turnos en MAR2
const sessionId = generateSessionId();
// Identificador de la variante MAR2 (modo libre)
const BOT_ID = "mar2";
let currentController = null;
const chatLog = document.getElementById("chat-log");
const form = document.getElementById("chat-form");
const input = document.getElementById("message");

// Construye la URL base de la API (autodetección o override global)
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

// Escapa HTML y reemplaza \n por <br> para formateo legible
function toSafeHtml(text) {
  const s = String(text ?? "");
  const escaped = s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
  return escaped.replace(/\n/g, "<br>");
}

// Agrega burbujas de conversación (usuario/bot) al log
const appendMessage = (role, text) => {
  const bubble = document.createElement("article");
  bubble.classList.add("message", role);
  bubble.innerHTML = toSafeHtml(text);
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
  if (!message) return;

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
        channel: "mar2", // activa el modo libre en el orquestador
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

// Mostrar resumen de configuración (temperature, top-p, max_tokens, pre-prompts)
function renderConfigSummary(settings) {
  try {
    const box = document.getElementById('config-summary');
    if (!box) return;
    const gen = settings?.generation || {};
    const temp = typeof gen.temperature === 'number' ? gen.temperature : 0.7;
    const topP = typeof gen.top_p === 'number' ? gen.top_p : 0.9;
    const maxT = typeof gen.max_tokens === 'number' ? gen.max_tokens : 256;
    const pre = Array.isArray(settings?.pre_prompts) ? settings.pre_prompts : [];

    box.innerHTML = '';
    const row = document.createElement('div');
    const kv1 = document.createElement('span'); kv1.className = 'kv'; kv1.innerHTML = `<b>Temperature:</b> ${temp}`;
    const kv2 = document.createElement('span'); kv2.className = 'kv'; kv2.innerHTML = `<b>Top‑p:</b> ${topP}`;
    const kv3 = document.createElement('span'); kv3.className = 'kv'; kv3.innerHTML = `<b>Max tokens:</b> ${maxT}`;
    row.appendChild(kv1); row.appendChild(kv2); row.appendChild(kv3);
    box.appendChild(row);

    if (pre.length > 0) {
      const label = document.createElement('div');
      label.className = 'hint';
      label.textContent = 'Pre‑prompts:';
      const chips = document.createElement('div');
      chips.className = 'chips';
      for (const p of pre) {
        const chip = document.createElement('span');
        chip.className = 'suggestion-chip';
        chip.textContent = p;
        chips.appendChild(chip);
      }
      box.appendChild(label);
      box.appendChild(chips);
    }
  } catch {}
}

// Sugerencias de menú: si hay configuradas para MAR2, mostrarlas como chips
(async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/chatbots/${BOT_ID}/settings?channel=mar2`, { cache: "no-cache" });
    if (!res.ok) return;
    const settings = await res.json();
    // Mostrar resumen de configuración
    renderConfigSummary(settings);
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

// Nota: a diferencia de app.js, acá no mostramos mensaje inicial por defecto.

// Botón Salir: aborta solicitud en curso y vuelve al portal (fail-safe)
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
    try { if (currentController) currentController.abort(); } catch {}
    window.location.href = "index.html";
  });
}

ensureExitButton();

// ================================================================
// Guía rápida (Cliente MAR2 – modo libre)
// ================================================================
//
// Comportamiento
// --------------
// - Envía mensajes a POST /chat/message con channel="mar2" y bot_id="mar2".
// - No usa menú inicial ni reglas: conversa directo con el LLM (o placeholder),
//   aunque puede mostrar un resumen de parámetros/pre_prompts provenientes del servidor.
//
// API_BASE_URL
// ------------
// - Autodetecta :8000 si se sirve el frontend en :5173. Sobrescribible con
//   window.WEBCHATBOT_API_BASE_URL.
//
// Consejos
// --------
// - Ajustar pre_prompts y parámetros de generación en el Portal para guiar el estilo.
// - Para reducir latencia, limitar max_tokens y evitar prompts excesivamente largos.
