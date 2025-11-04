# Arquitectura del Chatbot Municipal

## Visión general
```
Portal (selección) → Cliente Web → API (FastAPI) → Orquestador → {Reglas/FAQ | Buscador RAG | LLM}
                                      ↘ Moderación ↘ Handoff humano
```

## Capas
- **Interfaz**: portal de variantes + clientes web accesibles (maqueta estática actual; objetivo migrar a SPA con SSE/WebSocket).
- **API Gateway**: FastAPI con endpoints `POST /chat/message`, planeado agregar rate limiting y autenticación municipal.
- **Orquestador**: clasificador heurístico de intents, motor de reglas FAQ, RAG léxico en memoria y fallback LLM.
- **Adaptador LLM**: `LLMClient` intentará inicializar un modelo local (ruta provista por `scripts/export_webchatbot_env.sh`) y cae en placeholder cuando no está disponible.
- **Knowledge**: conjunto de FAQs en JSON como PoC; evolucionará hacia pipelines ETL y vector store gestionado.
- **Chatbots**: directorio `chatbots/` con metadatos por variante (id, nombre, canal, página frontend) para ampliar el portal y futuras configuraciones por bot.
- **Infraestructura**: pendiente de contenerización; visión incluye Docker, CI/CD y observabilidad (Prometheus/Grafana, OpenTelemetry).

## Flujos clave
1. **Conversación**: el usuario envía un mensaje → API valida payload → orquestador clasifica intent → responde con reglas, RAG o LLM.
2. **Handoff**: al detectar intent `handoff`, la API devuelve mensaje de derivación y marca `escalated=True` para atención humana.
3. **RAG**: el orquestador consulta `SimpleRagResponder`, que aplica similitud coseno sobre tokens normalizados para recuperar respuestas del JSON cargado desde `knowledge/faqs/municipal_faqs.json` vía `load_default_entries()`.

## Modelo de datos
- `ChatRequest` (`services/orchestrator/schema.py`) define `session_id`, `message` y `channel` (por defecto `"web"`).
- `ChatResponse` retorna los campos previos más `reply`, `source` (`faq`, `rag`, `llm`, `fallback`) y `escalated` para señalizar derivaciones humanas.

## Consideraciones de seguridad
- TLS end-to-end, anonimización de PII y retención controlada.
- Auditoría de conversaciones y revisión de contenido sensible.
- Pruebas de inyección de prompt, jailbreaking y moderación antes de emitir respuestas LLM.

## Próximos pasos
Consultar `docs/roadmap.md` para los hitos priorizados. El manual `docs/manual_aprendizaje.md` aporta pautas concretas para extender cada capa.
