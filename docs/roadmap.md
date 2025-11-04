# Roadmap Próximo (10 hitos)

1. Instrumentar logging estructurado y trazas OpenTelemetry en la API y el orquestador.
2. Incorporar pruebas de contrato para el endpoint `/chat/message` usando `httpx.AsyncClient`.
3. Añadir memoria de conversación (últimos turnos) y límites de contexto configurables.
4. Implementar módulo de moderación (listas de bloqueo, detección de PII básica) antes de invocar LLM.
5. Diseñar pipeline de ingestión (ETL) que normalice nuevas FAQs y actualice el índice RAG.
6. Persistir métricas clave (latencia, tasa de handoff, satisfacción) usando Redis/Prometheus.
7. Contenerizar API y frontend con Docker, incluyendo configuración de `docker-compose`.
8. Migrar el frontend a un framework (Vite + React) con componentes accesibles y tests E2E.
9. Integrar un vector store real (Chroma/Qdrant) y embeddings mediante `sentence-transformers`.
10. Configurar CI/CD (GitHub Actions) para ejecutar lint, tests y despliegue a entornos de staging.
