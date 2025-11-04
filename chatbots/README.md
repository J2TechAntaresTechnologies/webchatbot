# Portal de Chatbots

Este directorio contiene las variantes de chatbots y sus configuraciones.

Estructura sugerida por chatbot:
- `chatbots/<id>/config.json` → metadatos y parámetros básicos de la variante.
- (Opcional futuro) `chatbots/<id>/rules.json` → reglas específicas.
- (Opcional futuro) `chatbots/<id>/rag/` → fuentes y ajustes de RAG específicos.

Nota: Actualmente la API comparte un único cliente LLM y configuración global.
Las configuraciones por chatbot se usan principalmente desde el frontend (canal, título, descripción) y para planificación de futuras extensiones.

