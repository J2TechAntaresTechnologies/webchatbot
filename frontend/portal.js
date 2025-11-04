// Carga el listado de chatbots desde chatbots.json y renderiza tarjetas de selección.

// ==== Gestor de temas (frontend, localStorage) ====
(function themeManager() {
  const THEME_KEY = 'webchatbot_themes';
  const ACTIVE_KEY = 'webchatbot_active_theme';
  const VARS = ['--accent', '--accent-strong', '--surface', '--surface-bright', '--text-primary', '--text-secondary', '--font-family', '--font-size'];
  const RESERVED = ['default', 'light', 'dark'];

  function readVar(v) {
    const val = getComputedStyle(document.documentElement).getPropertyValue(v).trim();
    return val || '';
  }

  function rgbToHex(r, g, b) {
    const toHex = (n) => n.toString(16).padStart(2, '0');
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
  }

  function toHex(color) {
    if (!color) return '#000000';
    const c = color.trim();
    if (c.startsWith('#')) {
      if (c.length === 7) return c;
      // #rgb -> #rrggbb
      if (c.length === 4) return `#${c[1]}${c[1]}${c[2]}${c[2]}${c[3]}${c[3]}`;
      return c;
    }
    const m = c.match(/rgba?\((\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i);
    if (m) return rgbToHex(parseInt(m[1], 10), parseInt(m[2], 10), parseInt(m[3], 10));
    return '#000000';
  }

  function getDefaultTheme() {
    const vars = {};
    for (const k of VARS) {
      const raw = readVar(k);
      const isColor = k.startsWith('--accent') || k.startsWith('--surface') || k.startsWith('--text-');
      vars[k] = isColor ? toHex(raw) : raw;
    }
    return { name: 'default', vars };
  }

  function loadThemes() {
    const saved = (() => {
      try { return JSON.parse(localStorage.getItem(THEME_KEY) || '[]'); } catch { return []; }
    })();
    const userThemes = Array.isArray(saved)
      ? saved.filter(t => t && t.name && t.vars && !RESERVED.includes(String(t.name).toLowerCase()))
      : [];
    const def = getDefaultTheme();
    // Presets: dark (usa valores actuales) y light (valores claros)
    const dark = { name: 'dark', vars: Object.assign({}, def.vars) };
    const light = {
      name: 'light',
      vars: Object.assign({}, def.vars, {
        '--surface': '#ffffffcc',
        '--surface-bright': '#f8fafc',
        '--text-primary': '#0f172a',
        '--text-secondary': '#334155',
        '--accent': '#2563eb',
        '--accent-strong': '#7c3aed',
      })
    };
    return [def, dark, light, ...userThemes];
  }

  function saveThemes(list) {
    const data = list.filter(t => t && t.name && !RESERVED.includes(String(t.name).toLowerCase()));
    localStorage.setItem(THEME_KEY, JSON.stringify(data));
  }

  function applyThemeVars(vars) {
    const root = document.documentElement;
    for (const k of VARS) {
      if (vars && vars[k]) root.style.setProperty(k, vars[k]);
      else root.style.removeProperty(k);
    }
  }

  function setActiveTheme(name, themes) {
    localStorage.setItem(ACTIVE_KEY, name || 'default');
    const theme = (themes || loadThemes()).find(t => t.name === name) || getDefaultTheme();
    applyThemeVars(theme.vars);
    updateQuickSelect(themes || loadThemes());
  }

  function getActiveThemeName() {
    return localStorage.getItem(ACTIVE_KEY) || 'default';
  }

  // --- UI rápida en topbar ---
  function updateQuickSelect(themes) {
    const sel = document.getElementById('theme-select-quick');
    if (!sel) return;
    const list = themes || loadThemes();
    const active = getActiveThemeName();
    sel.innerHTML = '';
    for (const t of list) {
      const opt = document.createElement('option');
      opt.value = t.name;
      opt.textContent = t.name;
      if (t.name === 'default') opt.textContent = 'default';
      if (t.name === active) opt.selected = true;
      sel.appendChild(opt);
    }
  }

  function openThemeModal() {
    const backdrop = document.getElementById('theme-backdrop');
    if (!backdrop) return;
    backdrop.removeAttribute('hidden');

    const listEl = document.getElementById('theme-list');
    const nameEl = document.getElementById('theme-name');
    const inputs = {
      '--accent': document.getElementById('th-accent'),
      '--accent-strong': document.getElementById('th-accent-strong'),
      '--surface': document.getElementById('th-surface'),
      '--surface-bright': document.getElementById('th-surface-bright'),
      '--text-primary': document.getElementById('th-text-primary'),
      '--text-secondary': document.getElementById('th-text-secondary'),
      '--font-family': document.getElementById('th-font-family'),
      '--font-size': document.getElementById('th-font-size'),
    };

    const themes = loadThemes();
    listEl.innerHTML = '';
    for (const t of themes) {
      const opt = document.createElement('option');
      opt.value = t.name;
      opt.textContent = t.name;
      listEl.appendChild(opt);
    }
    listEl.value = getActiveThemeName();

    function fillInputs(theme) {
      for (const k of VARS) {
        const el = inputs[k];
        if (!el) continue;
        const raw = theme.vars[k] || readVar(k);
        if (el.type === 'color') el.value = toHex(raw);
        else el.value = String(raw || '');
      }
      nameEl.value = theme.name === 'default' ? '' : theme.name;
    }

    function currentThemeObj() {
      const vars = {};
      for (const k of VARS) {
        const el = inputs[k];
        if (!el) continue;
        let v = el.value || readVar(k) || '';
        if (k === '--font-size') {
          // Normalizar a px si es numérico
          v = /\d$/.test(v) ? `${v}px` : v;
        }
        vars[k] = v;
      }
      return { name: listEl.value || 'default', vars };
    }

    const selectedTheme = themes.find(t => t.name === listEl.value) || themes[0];
    fillInputs(selectedTheme);

    // Handlers
    document.getElementById('theme-apply').onclick = () => {
      const vars = {};
      for (const k of VARS) vars[k] = inputs[k].value;
      applyThemeVars(vars);
      setActiveTheme(listEl.value, themes);
    };

    document.getElementById('theme-save').onclick = () => {
      const name = (nameEl.value || '').trim();
      if (!name) { alert('Ingresá un nombre para guardar el tema'); return; }
      if (name === 'default') { alert('No podés sobrescribir el tema default'); return; }
      const list = loadThemes();
      const exists = list.some(t => t.name === name);
      const vars = {};
      for (const k of VARS) vars[k] = inputs[k].value;
      const newList = exists ? list.map(t => t.name === name ? { name, vars } : t) : [...list, { name, vars }];
      saveThemes(newList);
      updateQuickSelect(newList);
      // Seleccionar nuevo
      document.getElementById('theme-select-quick').value = name;
      setActiveTheme(name, newList);
      // Actualizar lista del modal
      if (!exists) {
        const opt = document.createElement('option');
        opt.value = name;
        opt.textContent = name;
        listEl.appendChild(opt);
      }
      listEl.value = name;
      alert('Tema guardado');
    };

    document.getElementById('theme-update').onclick = () => {
      const sel = listEl.value;
      if (RESERVED.includes(String(sel).toLowerCase())) { alert('Este tema predefinido no se puede actualizar. Guardá uno nuevo.'); return; }
      const list = loadThemes();
      const vars = {};
      for (const k of VARS) vars[k] = inputs[k].value;
      const newList = list.map(t => t.name === sel ? { name: sel, vars } : t);
      // Filtrar reservados antes de persistir
      saveThemes(newList.filter(t => !RESERVED.includes(String(t.name).toLowerCase())));
      updateQuickSelect(newList);
      setActiveTheme(sel, newList);
      alert('Tema actualizado');
    };

    document.getElementById('theme-delete').onclick = () => {
      const sel = listEl.value;
      if (RESERVED.includes(String(sel).toLowerCase())) { alert('Este tema predefinido no se puede borrar'); return; }
      const list = loadThemes();
      const newList = list.filter(t => t.name !== sel);
      saveThemes(newList.filter(t => !RESERVED.includes(String(t.name).toLowerCase())));
      updateQuickSelect(newList);
      const fallback = 'default';
      setActiveTheme(fallback, newList);
      listEl.value = fallback;
      fillInputs(getDefaultTheme());
      // Remover opción del modal
      const opt = Array.from(listEl.options).find(o => o.value === sel);
      if (opt) opt.remove();
      alert('Tema eliminado');
    };

    const resetBtn = document.getElementById('theme-reset');
    if (resetBtn) {
      resetBtn.onclick = () => {
        // Eliminar cualquier tema guardado que intente sobreescribir los predefinidos
        try {
          const saved = JSON.parse(localStorage.getItem(THEME_KEY) || '[]');
          const filtered = Array.isArray(saved) ? saved.filter(t => !RESERVED.includes(String(t?.name || '').toLowerCase())) : [];
          localStorage.setItem(THEME_KEY, JSON.stringify(filtered));
        } catch {}
        const themes = loadThemes();
        updateQuickSelect(themes);
        setActiveTheme('default', themes);
        listEl.value = 'default';
        fillInputs(getDefaultTheme());
        alert('Temas predefinidos restablecidos (light/dark). Tus temas guardados permanecen.');
      };
    }

    document.getElementById('theme-close').onclick = () => {
      backdrop.setAttribute('hidden', '');
    };

    // Cambiar selección y previsualizar
    listEl.onchange = () => {
      const t = loadThemes().find(x => x.name === listEl.value) || getDefaultTheme();
      fillInputs(t);
      applyThemeVars(t.vars);
      setActiveTheme(t.name);
    };

    // Cerrar clic fuera
    backdrop.onclick = (ev) => { if (ev.target === backdrop) backdrop.setAttribute('hidden', ''); };
    document.onkeydown = (ev) => { if (ev.key === 'Escape') backdrop.setAttribute('hidden', ''); };
  }

  function init() {
    // Aplicar activo
    const themes = loadThemes();
    updateQuickSelect(themes);
    const active = getActiveThemeName();
    const theme = themes.find(t => t.name === active) || themes[0];
    applyThemeVars(theme.vars);

    const quick = document.getElementById('theme-select-quick');
    if (quick) {
      quick.onchange = () => setActiveTheme(quick.value);
    }
    const openBtn = document.getElementById('theme-open');
    if (openBtn) openBtn.addEventListener('click', openThemeModal);
  }

  // Inicializar al cargar
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

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

async function loadChatbots() {
  try {
    const res = await fetch('chatbots.json', { cache: 'no-cache' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('Error cargando chatbots.json', err);
    return [];
  }
}

function renderList(items) {
  const list = document.getElementById('bot-list');
  list.innerHTML = '';
  if (!Array.isArray(items) || items.length === 0) {
    const empty = document.createElement('p');
    empty.textContent = 'No hay chatbots registrados.';
    empty.className = 'hint';
    list.appendChild(empty);
    return;
  }

  for (const bot of items) {
    const card = document.createElement('article');
    card.className = 'message bot';
    const title = document.createElement('h2');
    title.textContent = bot.name || bot.id;
    const desc = document.createElement('p');
    desc.textContent = bot.description || '';
    const actions = document.createElement('div');
    actions.style.marginTop = '0.5rem';
    const link = document.createElement('a');
    link.href = bot.frontend_page || '#';
    link.textContent = 'Abrir';
    link.setAttribute('role', 'button');
    link.className = 'btn-link';
    const paramsBtn = document.createElement('button');
    paramsBtn.type = 'button';
    paramsBtn.textContent = 'Parámetros';
    paramsBtn.style.marginLeft = '0.5rem';
    paramsBtn.addEventListener('click', () => openSettingsModal(bot));
    actions.appendChild(link);
    actions.appendChild(paramsBtn);
    card.appendChild(title);
    card.appendChild(desc);
    card.appendChild(actions);
    list.appendChild(card);
  }
}

loadChatbots().then(renderList);

// --- Modal de configuración ---
let currentBot = null;
let currentSettings = null;

function setFeedback(msg, isError = false) {
  const el = document.getElementById('settings-feedback');
  if (!el) return;
  el.textContent = msg || '';
  el.style.color = isError ? '#fca5a5' : 'var(--text-secondary)';
}

function showBackdrop(show) {
  const el = document.getElementById('settings-backdrop');
  if (!el) return;
  if (show) {
    el.removeAttribute('hidden');
  } else {
    el.setAttribute('hidden', '');
  }
}

async function fetchSettings(bot) {
  const url = `${API_BASE_URL}/chatbots/${encodeURIComponent(bot.id)}/settings?channel=${encodeURIComponent(bot.channel || '')}`;
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

async function saveSettings(bot, settings) {
  const url = `${API_BASE_URL}/chatbots/${encodeURIComponent(bot.id)}/settings`;
  const res = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

async function resetSettings(bot) {
  const url = `${API_BASE_URL}/chatbots/${encodeURIComponent(bot.id)}/settings/reset?channel=${encodeURIComponent(bot.channel || '')}`;
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

function renderSuggestionsEditor(listEl, items) {
  listEl.innerHTML = '';
  const data = Array.isArray(items) ? items.slice() : [];
  for (let i = 0; i < data.length; i++) {
    const row = document.createElement('div');
    row.className = 'row';
    const lab = document.createElement('input');
    lab.placeholder = 'Etiqueta';
    lab.value = data[i].label || '';
    const msg = document.createElement('input');
    msg.placeholder = 'Mensaje';
    msg.value = data[i].message || '';
    const del = document.createElement('button');
    del.type = 'button';
    del.textContent = '✕';
    del.addEventListener('click', () => {
      row.remove();
    });
    row.appendChild(lab);
    row.appendChild(msg);
    row.appendChild(del);
    listEl.appendChild(row);
  }
}

function renderPrepromptsEditor(listEl, items) {
  listEl.innerHTML = '';
  const data = Array.isArray(items) ? items.slice() : [];
  for (let i = 0; i < data.length; i++) {
    const row = document.createElement('div');
    row.className = 'row';
    const txt = document.createElement('input');
    txt.placeholder = 'Instrucción (ej.: "Responde de forma breve")';
    txt.value = (data[i] || '').toString();
    const del = document.createElement('button');
    del.type = 'button';
    del.textContent = '✕';
    del.addEventListener('click', () => row.remove());
    row.appendChild(txt);
    row.appendChild(del);
    listEl.appendChild(row);
  }
}

function collectSuggestions(listEl) {
  const rows = Array.from(listEl.querySelectorAll('.row'));
  const items = [];
  for (const r of rows) {
    const [lab, msg] = r.querySelectorAll('input');
    const label = (lab?.value || '').trim();
    const message = (msg?.value || '').trim();
    if (label && message) items.push({ label, message });
  }
  return items;
}

function collectPreprompts(listEl) {
  const rows = Array.from(listEl.querySelectorAll('.row'));
  const items = [];
  for (const r of rows) {
    const txt = r.querySelector('input');
    const val = (txt?.value || '').trim();
    if (val) items.push(val);
  }
  return items;
}

async function openSettingsModal(bot) {
  currentBot = bot;
  showBackdrop(true);
  const temp = document.getElementById('stg-temperature');
  const topp = document.getElementById('stg-topp');
  const maxt = document.getElementById('stg-maxtokens');
  const useRules = document.getElementById('stg-userules');
  const useRag = document.getElementById('stg-userag');
  const list = document.getElementById('stg-suggestions');
  const preList = document.getElementById('stg-preprompts');
  try {
    const settings = await fetchSettings(bot);
    currentSettings = settings;
    temp.value = settings.generation?.temperature ?? 0.7;
    topp.value = settings.generation?.top_p ?? 0.9;
    maxt.value = settings.generation?.max_tokens ?? 256;
    useRules.checked = !!(settings.features?.use_rules ?? true);
    useRag.checked = !!(settings.features?.use_rag ?? true);
    renderSuggestionsEditor(list, settings.menu_suggestions || []);
    renderPrepromptsEditor(preList, settings.pre_prompts || []);
    setFeedback('');
  } catch (e) {
    console.error('No se pudieron cargar parámetros', e);
    setFeedback('No se pudieron cargar parámetros. Verificá la API.', true);
  }

  const addBtn = document.getElementById('stg-add-suggestion');
  addBtn.onclick = () => {
    const row = document.createElement('div');
    row.className = 'row';
    const lab = document.createElement('input');
    lab.placeholder = 'Etiqueta';
    const msg = document.createElement('input');
    msg.placeholder = 'Mensaje';
    const del = document.createElement('button');
    del.type = 'button';
    del.textContent = '✕';
    del.addEventListener('click', () => row.remove());
    row.appendChild(lab);
    row.appendChild(msg);
    row.appendChild(del);
    list.appendChild(row);
  };

  const addPreBtn = document.getElementById('stg-add-preprompt');
  addPreBtn.onclick = () => {
    const row = document.createElement('div');
    row.className = 'row';
    const txt = document.createElement('input');
    txt.placeholder = 'Instrucción (ej.: "Responde de forma breve")';
    const del = document.createElement('button');
    del.type = 'button';
    del.textContent = '✕';
    del.addEventListener('click', () => row.remove());
    row.appendChild(txt);
    row.appendChild(del);
    preList.appendChild(row);
  };

  document.getElementById('settings-cancel').onclick = () => showBackdrop(false);
  // Cerrar al hacer click fuera del cuadro
  const backdrop = document.getElementById('settings-backdrop');
  backdrop.onclick = (ev) => {
    if (ev.target === backdrop) showBackdrop(false);
  };
  // Cerrar con tecla ESC
  document.onkeydown = (ev) => {
    if (ev.key === 'Escape') showBackdrop(false);
  };
  document.getElementById('settings-save').onclick = async () => {
    // Parseo robusto con fallback a valores actuales
    const parseNum = (v) => (Number.isFinite(Number(v)) ? Number(v) : null);
    const ct = currentSettings?.generation?.temperature ?? 0.7;
    const cp = currentSettings?.generation?.top_p ?? 0.9;
    const cm = currentSettings?.generation?.max_tokens ?? 256;

    let t = parseNum(temp.value);
    let p = parseNum(topp.value);
    let m = parseNum(maxt.value);
    t = t === null ? ct : Math.min(Math.max(t, 0), 2);
    p = p === null ? cp : Math.min(Math.max(p, 0), 1);
    m = m === null ? cm : Math.max(Math.floor(m), 1);

    if (!Number.isFinite(t) || !Number.isFinite(p) || !Number.isFinite(m)) {
      setFeedback('Parámetros inválidos. Revisá los campos numéricos.', true);
      return;
    }

    const payload = {
      generation: {
        temperature: t,
        top_p: p,
        max_tokens: m,
      },
      features: {
        use_rules: !!useRules.checked,
        use_rag: !!useRag.checked,
      },
      menu_suggestions: collectSuggestions(list),
      pre_prompts: collectPreprompts(preList),
    };
    try {
      await saveSettings(bot, payload);
      setFeedback('Guardado.');
      showBackdrop(false);
    } catch (e) {
      console.error('Error guardando', e);
      setFeedback('Error guardando. Verificá la API.', true);
    }
  };
  document.getElementById('settings-reset').onclick = async () => {
    try {
      const settings = await resetSettings(bot);
      currentSettings = settings;
      temp.value = settings.generation?.temperature ?? 0.7;
      topp.value = settings.generation?.top_p ?? 0.9;
      maxt.value = settings.generation?.max_tokens ?? 256;
      useRules.checked = !!(settings.features?.use_rules ?? true);
      useRag.checked = !!(settings.features?.use_rag ?? true);
      renderSuggestionsEditor(list, settings.menu_suggestions || []);
      setFeedback('Valores restablecidos.');
    } catch (e) {
      console.error('Error restableciendo', e);
      setFeedback('Error al restablecer. Verificá la API.', true);
    }
  };
}

// --- Ayuda ---
function showHelp(show) {
  const el = document.getElementById('help-backdrop');
  if (!el) return;
  if (show) el.removeAttribute('hidden');
  else el.setAttribute('hidden', '');
}

const helpBtn = document.getElementById('settings-help');
if (helpBtn) {
  helpBtn.addEventListener('click', () => showHelp(true));
}

const helpClose = document.getElementById('help-close');
if (helpClose) {
  helpClose.addEventListener('click', () => showHelp(false));
}

const helpBackdrop = document.getElementById('help-backdrop');
  if (helpBackdrop) {
    helpBackdrop.onclick = (ev) => {
      if (ev.target === helpBackdrop) showHelp(false);
    };
  }

// ================================================================
// Guía rápida (Portal de Chatbots y parametrización)
// ================================================================
//
// ¿Qué hace?
// -----------
// - Renderiza las variantes definidas en frontend/chatbots.json.
// - Permite abrir un modal de Configuración por bot y guardar parámetros
//   persistentes en el servidor vía /chatbots/{id}/settings.
// - Gestiona temas (colores) en localStorage y aplica el activo en tiempo real.
//
// Endpoints usados
// ----------------
// - GET  /chatbots/{id}/settings?channel=<canal>
// - PUT  /chatbots/{id}/settings
// - POST /chatbots/{id}/settings/reset?channel=<canal>
//
// API_BASE_URL
// ------------
// - Autodetecta :8000 en el mismo host si está en :5173.
// - Se puede forzar con: <script>window.WEBCHATBOT_API_BASE_URL="https://api.miservicio.com";</script>
//
// Consejos
// --------
// - Guardar cambios escribe chatbots/<id>/settings.json en el servidor.
// - Los valores numéricos se validan y el backend los limita a rangos seguros.
// - No hay autenticación por defecto: proteger la API si se expone públicamente.
