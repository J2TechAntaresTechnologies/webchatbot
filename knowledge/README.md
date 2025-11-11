# Knowledge Base

Scripts y datasets para alimentar el chatbot con información oficial.

## Estructura actual
- `faqs/`: preguntas frecuentes en JSON/CSV. Incluye `municipal_faqs.json`, usado por el RAG léxico en memoria.
- `00relevamientos_j2/munivilladata/` (raíz del repo): textos `.txt` curatoriales que la API indexa automáticamente al iniciar (párrafos largos). Sirven como contexto adicional para respuestas.
- `documents/`: normativa municipal, comunicados (pendiente).
- `embeddings/`: vectores generados para RAG con modelos reales (pendiente).

## Formato de FAQs (JSON/JSONC)
- Archivo: `knowledge/faqs/municipal_faqs.json` (admite comentarios JSONC: `//` línea y bloque `/* ... */`).
- Cada entrada debe incluir `uid`, `question`, `answer`, `tags` (lista de strings minúsculos):
```
{
  "uid": "faq-001",
  "question": "¿Dónde puedo consultar ordenanzas municipales?",
  "answer": "Las ordenanzas vigentes están disponibles en ordenanzas.municipio.gob...",
  "tags": ["ordenanza", "documentacion", "normativa"]
}
```
- Recomendaciones:
  - `uid` único y estable (ej: `faq-005`).
  - Pregunta breve y concreta; respuesta clara con enlaces o rutas del portal.
  - `tags` en minúscula, 2–4 términos que faciliten el match léxico (sin tildes).
  - Si usás utilidades como `jq`, recordá que no soportan comentarios: quitá comentarios antes de parsear.

## Cómo extender la base
1. **Agregar nuevas FAQs**
   - Duplicar `municipal_faqs.json` o crear un CSV con columnas `uid,question,answer,tags`.
   - Mantener `uid` únicos y tags en minúscula para facilitar filtrado.
2. **Actualizar el RAG**
   - JSON: editar `knowledge/faqs/municipal_faqs.json` (admite comentarios JSONC) y reiniciar la API.
   - TXT: agregar/editar `.txt` en `00relevamientos_j2/munivilladata/` y reiniciar la API (se indexan por párrafos largos).
3. **Construir embeddings reales**
   - Generar vectores en `embeddings/` usando `sentence-transformers` u otro modelo.
   - Sustituir `SimpleRagResponder` por un conector a Chroma/Qdrant (ver `docs/manual_aprendizaje.md`).

## Buenas prácticas
- Versionar fuentes originales y derivados por separado.
- Validar campos obligatorios (uid, pregunta, respuesta) antes de publicar.
- Documentar procedencia y fecha de actualización de cada lote de datos.

## Generación con contexto (Grounded)
- Cuando no hay respuesta directa por Reglas/RAG, el orquestador puede invocar el LLM con contexto: toma los mejores pasajes (top‑k) de la KB y construye un prompt que exige “usar solo el contexto”.
- Si `grounded_only` está activo y no hay pasajes relevantes, se abstiene de responder.

## Validación rápida
- Validar JSON: `jq . knowledge/faqs/municipal_faqs.json >/dev/null` (sale con código 0 si es válido).
- Contar FAQs: `jq 'length' knowledge/faqs/municipal_faqs.json`.
- Ver primeras preguntas: `jq -r '.[].question' knowledge/faqs/municipal_faqs.json | head`.

## Próximos pasos
1. Consolidar las fuentes oficiales y definir esquema de metadatos.
2. Implementar ETL (`knowledge/etl_*.py`) con validaciones y versionado.
3. Configurar vector store (Chroma/Qdrant) y pipelines de actualización.
