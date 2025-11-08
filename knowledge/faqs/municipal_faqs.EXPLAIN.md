Municipal FAQs Dataset — Explicación y Guía de Campos
=====================================================

Resumen
-------
Este archivo documenta el dataset `municipal_faqs.json`, que alimenta el componente
RAG ligero (`SimpleRagResponder`) del orquestador. El RAG vectoriza en memoria las
entradas y recupera una respuesta basada en similitud léxica.

Cómo lo usa el sistema
----------------------
- Carga: `services/orchestrator/rag.py:158` (función `load_default_entries`) lee
  `municipal_faqs.json` y crea objetos `KnowledgeEntry` (uid, question, answer, tags).
- Indexación: `SimpleRagResponder` concatena `question + tags` y crea un vector TF
  (bag-of-words normalizado). Ver `services/orchestrator/rag.py:130`.
- Búsqueda: En consulta, compara por similitud de coseno y aplica un umbral (`threshold`).
  Si el mejor score < threshold, no devuelve respuesta (cae a siguiente fase del orquestador).

Estructura del archivo JSON
---------------------------
- Formato: una lista (array JSON) de objetos.
- Cada objeto representa una FAQ con los campos: `uid`, `question`, `answer`, `tags`.
- Importante: el archivo debe ser JSON válido estándar (sin comentarios) ya que se
  parsea con `json.load`.

Ejemplo mínimo de entrada
-------------------------
{
  "uid": "faq-001",
  "question": "¿Dónde puedo consultar ordenanzas municipales?",
  "answer": "Las ordenanzas vigentes están disponibles en ordenanzas.municipio.gob...",
  "tags": ["ordenanza", "documentacion", "normativa"]
}

Descripción de parámetros (por campo)
-------------------------------------
- uid (string)
  - Propósito: identificador único y estable de la entrada. Ayuda a trazabilidad,
    versionado y depuración.
  - Formato: libre (ej.: `faq-001`). Evitar espacios. No duplicar UIDs.
  - Impacto: no afecta el matching, pero es clave para mantenimiento.

- question (string)
  - Propósito: pregunta canónica que los usuarios suelen formular.
  - Recomendaciones: clara y concisa (1 oración). Evitar jergas internas.
  - Impacto: se vectoriza y contribuye directamente a la similitud. Palabras
    relevantes mejoran el score.

- answer (string)
  - Propósito: respuesta oficial que verá el usuario si se recupera la entrada.
  - Recomendaciones: precisa, actualizada, con enlaces/rutas. Longitud sugerida < 800 chars.
  - Impacto: es lo que se devuelve sin modificación. No influye en el score.

- tags (array de string)
  - Propósito: keywords/etiquetas que amplían la señal semántica para mejorar el recall.
  - Recomendaciones: 2–4 tags, en minúsculas, sin tildes (el sistema normaliza, pero
    mantener consistencia ayuda). Evitar términos demasiado genéricos.
  - Impacto: se concatenan a `question` para la vectorización; influyen en el score.

Buenas prácticas de contenido
----------------------------
- Usar vocabulario ciudadano y términos frecuentes de búsqueda.
- Mantener consistencia en tags y revisar duplicados/variantes (ej.: `poda` vs `podas`).
- Revisar y actualizar respuestas ante cambios normativos/procedimentales.

Validación rápida (opcional)
----------------------------
- Validar JSON: `jq . knowledge/faqs/municipal_faqs.json >/dev/null`
- Contar entradas: `jq 'length' knowledge/faqs/municipal_faqs.json`
- Ver preguntas: `jq -r '.[].question' knowledge/faqs/municipal_faqs.json | head`

Limitaciones conocidas
----------------------
- El RAG usa bag-of-words sin IDF ni stemming: términos muy frecuentes pueden
  pesar más de lo deseado. Compensar con buenos `tags` y redacción de `question`.
- El dataset se indexa al iniciar el servicio; cambios en el JSON requieren reinicio
  para que se reflejen.

