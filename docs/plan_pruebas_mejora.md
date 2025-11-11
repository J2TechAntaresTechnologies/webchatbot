# Plan de Pruebas e Indicadores de Mejora (Munivilla)

Este documento sirve como guía y planilla para probar el chatbot municipal, recolectar resultados y decidir mejoras iterativas. Se enfoca en la cobertura por fuente (Reglas, RAG, LLM), exactitud percibida, latencia y robustez.

## 1) Objetivos y alcance
- Validar que las consultas frecuentes se resuelven por la fuente correcta (Reglas → RAG → Genérico → LLM).
- Medir exactitud por categoría y fuente; detectar falsos positivos/negativos de RAG y gaps de Reglas.
- Estimar latencia percibida (tiempo end‑to‑end) y facilidad de uso (menú/ayuda).
- Sugerir ajustes de: `rules`, `knowledge/faqs/*.json` (KB RAG), `rag_threshold`, `intent patterns` y `pre_prompts`.

Alcance: canal Municipal (web). Opcional: sanity en MAR2 (libre).

## 2) Preparación del entorno
- Levantar servicios: `./start_noverbose.sh` (o `./start.sh`).
- Confirmar modelo LLM o placeholder; KB cargada desde `knowledge/faqs/municipal_faqs.json`.
- Nota: cada cambio en KB requiere reiniciar la API para reindexar.
- Registrar versión/commit/tag:
  - Versión/tag: …
  - `rag_threshold`: … (p.ej. 0.28)
  - generation: temperature …, top_p …, max_tokens …

## 3) Métricas clave (definiciones)
- Cobertura por fuente: % de casos que responden por Regla / RAG / Genérico / LLM.
- Exactitud percibida:
  - Regla: Correcta (S/N) y “alineación” con política/área.
  - RAG: Correcta (S/N) + “Relevancia” (1‑5). Contar FP (respondió mal) y FN (no respondió aunque hay entrada).
  - LLM: Utilidad (1‑5) y Corrección factual (S/N).
- Latencia: tiempo end‑to‑end (segundos, estimado manual o medido por cronómetro).
- Intents: % de casos que se encaminaron al intent esperado (faq/rag/…)
- Satisfacción: rating 1–5 (subjetivo) por caso.

## 4) Matriz de casos (llenar durante pruebas)
Use la tabla por cada categoría. Copiar/pegar respuesta textualmente y marcar campos.

| Caso | Prompt | Intención esperada | Fuente esp. | Respuesta (copiar breve) | Fuente obs. | Correcta (S/N) | Latencia (s) | Observaciones | Acción/Mejora |
|---|---|---|---|---|---|---|---|---|---|
| 1 | turno licencia de conducir | faq | regla | … | … | S | 1.8 | link verificable | n/a |
| 2 | proveedores inscribirme | rag | rag | … | … | N | 2.2 | devolvió genérico | agregar patrón/entrada |

### 4.1 Bienestar y Salud
Guía: amsa, cic, consumos, punto violeta, discapacidad, dengue.

Casos sugeridos:
- “consumos problemáticos” (RAG)
- “punto violeta” (RAG)
- “certificado discapacidad requisitos” (Regla o RAG)
- “AMSA turno” (RAG)
- “campaña dengue” (RAG)

### 4.2 Educación y Juventud
- “juventud actividades” (RAG)
- “Congreso CER” (RAG)
- “economía social apoyo emprendimientos” (RAG)

### 4.3 Trámites y Gestiones
- “trámites online” (RAG)
- “turno licencia” (Regla)
- “inscribirse proveedor municipal” (RAG/Regla)
- “libre deuda” (RAG)
- “seguimiento de expediente” (RAG)

### 4.4 Cultura, Turismo y Ambiente
- “agenda cultural” (RAG)
- “atractivos turísticos” (RAG)
- “villa más limpia separación” (RAG)

### 4.5 Desarrollo Urbano y Comercio
- “obras privadas requisitos” (Regla)
- “habilitaciones comerciales” (RAG)

### 4.6 Información y Contacto
- “emergencias” (Regla)
- “policía” (Regla)
- “horarios de atención” (Regla)
- “contacto” (Regla)

## 5) Cálculo de indicadores (llenar al finalizar)
- Totales por fuente: Regla = … / … (% …), RAG = … / … (% …), Genérico = … (% …), LLM = … (% …)
- Exactitud por fuente:
  - Regla: … correctas / … (…%)
  - RAG: … correctas / … (…%), FP = …, FN = …
  - LLM: Útiles (≥4/5) = … / … (…%)
- Intents correctos: … / … (…%)
- Latencia media: … s (p95: … s)
- Satisfacción media: … / 5

## 6) Guía de diagnóstico y mejoras
- Si Regla no dispara pero debería: añadir `rules[]` en `chatbots/municipal/settings.json` con stems y opcional `min_matches`.
- Si RAG no responde (FN): crear/ajustar entrada en `knowledge/faqs/municipal_faqs.json` (question clara, tags relevantes) o bajar `rag_threshold` (p. ej. 0.26).
- Si RAG responde mal (FP): subir `rag_threshold` (p. ej. 0.32), mejorar `tags`/question y añadir una Regla específica si conviene.
- Si el clasificador envía a la fuente incorrecta: agregar `IntentPattern` con stems (services/orchestrator/intent_classifier.py).
- Si LLM divaga: bajar `temperature`/`top_p`, recortar `max_tokens`, ajustar `pre_prompts`.

## 7) Plan de tuning recomendado
- RAG threshold sweep: 0.26 / 0.28 / 0.32 → medir RAG hit, FP, FN y elegir compromiso.
- Reglas: definir `min_matches` (p. ej. proveedores=2) para reducir falsos positivos.
- Clasificador: añadir patrones para consultas recurrentes (p. ej. “inscribirme”, “trámite online”).
- Chips (menu_suggestions): añadir accesos frecuentes hallados en pruebas.

## 8) Robustez y seguridad (pruebas sugeridas)
- Ambigüedad: “quiero hacer un trámite”, “necesito ayuda”.
- Variantes lingüísticas/errores: “probedor inscribirme”, “polisia”, “discapasidad”.
- Inyección o contenido inapropiado: que el bot no invente ni dé instrucciones peligrosas; remitir a fuentes oficiales.

## 9) Registro y backlog
- Registra fecha, commit/tag, configuración, y adjunta logs relevantes.
- Backlog de mejoras priorizado (Top‑5):
  1. …
  2. …
  3. …
  4. …
  5. …

---

Plantilla de tabla adicional (copiar según necesidad):

| Caso | Prompt | Intención esp. | Fuente esp. | Respuesta | Fuente obs. | Correcta | Latencia | Observaciones | Acción |
|---|---|---|---|---|---|---|---|---|---|
