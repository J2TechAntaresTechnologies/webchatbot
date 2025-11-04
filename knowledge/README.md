# Knowledge Base

Scripts y datasets para alimentar el chatbot con información oficial.

## Estructura actual
- `faqs/`: preguntas frecuentes en JSON/CSV. Incluye `municipal_faqs.json`, usado por el RAG léxico en memoria.
- `documents/`: normativa municipal, comunicados (pendiente).
- `embeddings/`: vectores generados para RAG con modelos reales (pendiente).

## Formato de FAQs (JSON)
- Archivo: `knowledge/faqs/municipal_faqs.json`.
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

## Cómo extender la base
1. **Agregar nuevas FAQs**
   - Duplicar `municipal_faqs.json` o crear un CSV con columnas `uid,question,answer,tags`.
   - Mantener `uid` únicos y tags en minúscula para facilitar filtrado.
2. **Actualizar el RAG**
   - Correr un script ETL (por crear) que normalice las fuentes y exporte un JSON compatible.
   - Reiniciar la API o invocar `ChatOrchestrator.attach_rag(...)` con el nuevo dataset.
3. **Construir embeddings reales**
   - Generar vectores en `embeddings/` usando `sentence-transformers` u otro modelo.
   - Sustituir `SimpleRagResponder` por un conector a Chroma/Qdrant (ver `docs/manual_aprendizaje.md`).

## Buenas prácticas
- Versionar fuentes originales y derivados por separado.
- Validar campos obligatorios (uid, pregunta, respuesta) antes de publicar.
- Documentar procedencia y fecha de actualización de cada lote de datos.

## Validación rápida
- Validar JSON: `jq . knowledge/faqs/municipal_faqs.json >/dev/null` (sale con código 0 si es válido).
- Contar FAQs: `jq 'length' knowledge/faqs/municipal_faqs.json`.
- Ver primeras preguntas: `jq -r '.[].question' knowledge/faqs/municipal_faqs.json | head`.

## Próximos pasos
1. Consolidar las fuentes oficiales y definir esquema de metadatos.
2. Implementar ETL (`knowledge/etl_*.py`) con validaciones y versionado.
3. Configurar vector store (Chroma/Qdrant) y pipelines de actualización.
