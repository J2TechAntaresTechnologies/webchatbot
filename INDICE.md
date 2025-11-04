# Índice de Documentación del Proyecto

Este índice centraliza la documentación del repositorio: ubicación de cada documento, su propósito y el temario (secciones principales) para navegación rápida.

Nota: este índice cubre sólo archivos propios del proyecto. Se excluyen documentos de paquetes del entorno virtual en `lib/`.

## Documentos principales

- `README.md` — Descripción general, instalación y uso.
  - Temario: Componentes previstos; Estructura del repositorio; Estado actual; Instalación; Ejecución local; Contrato del endpoint `/chat/message`; Acceso externo (sin DNS); Pruebas; Configurar un LLM local; Diagnóstico del host; Próximos pasos sugeridos; Documentación relacionada.

- `docs/operacion_configuracion_chatbots.md` — Operación, configuración de chatbots y gestión de prompts.
  - Temario: Dónde se alojan prompts/params/archivos persistentes; Tutorial paso a paso (Portal/API/archivos) con consejos; Efecto de logs y parámetros en el bot; Guía de prompts (estrategias, versionado y archivos sugeridos); Apéndice de rutas y referencias.

- `docs/architecture.md` — Arquitectura técnica del sistema.
  - Temario: Visión general; Capas; Flujos clave; Modelo de datos; Consideraciones de seguridad; Próximos pasos.

- `docs/manual_aprendizaje.md` — Manual para aprender y modificar el proyecto.
  - Temario: 1) Ruta de aprendizaje sugerida; 2) Arquitectura y responsabilidades; 3) Flujo de desarrollo recomendado; 4) Modificar el orquestador (4.1 Añadir nuevos intents; 4.2 Sustituir el motor de reglas; 4.3 Integrar un RAG real; 4.4 Conectar con un LLM; 4.5 Agregar una nueva variante al portal); 5) Trabajo con la base de conocimiento; 6) Seguridad y compliance; 7) Pruebas y calidad; 8) Frontend: lineamientos; 9) Entrega y despliegue; 10) Recursos adicionales.

- `docs/guia_tecnologias_avanzada.md` — Guía avanzada de tecnologías y operación.
  - Temario: 1) Mapa tecnológico y responsabilidades; 2) Stack detallado por componente (2.1 Frontend estático; 2.2 API Gateway con FastAPI; 2.3 Modelado con Pydantic v2; 2.4 Orquestador central; 2.5 Recuperación aumentada (RAG); 2.6 Integración LLM; 2.7 Configuración y despliegue); 3) Tutorial paso a paso (3.1 Preparación del entorno; 3.2 Levantar servicios; 3.3 Personalizar la base de conocimiento; 3.4 Añadir un intent nuevo; 3.5 Conectar un modelo LLM real; 3.6 Encender observabilidad); 4) Licencias y consideraciones.

- `docs/roadmap.md` — Próximos 10 hitos prioritarios.
  - Temario: Logging y OpenTelemetry; Pruebas de contrato; Memoria de conversación; Moderación/PII; ETL de FAQs e índice RAG; Métricas (Redis/Prometheus); Docker y `docker-compose`; Migración frontend (Vite/React) + E2E; Vector store (Chroma/Qdrant) + embeddings; CI/CD (lint, tests, deploy).

- `portal/README.md` — Guía del Portal de Chatbots (estructura y operación).
  - Temario: Objetivo; Estructura del proyecto (resumen); Cambios clave; Parámetros y configuración; Ejecución; Cómo agregar un nuevo chatbot (paso a paso); Extender el backend por variante (opcional); Parametrización del frontend y API base; Comandos útiles; Buenas prácticas; FAQ.

- `frontend/README.md` — Uso del portal y clientes web.
  - Temario: Uso rápido; Temas (colores) y persistencia; Parámetros visibles en MAR2; Próximos pasos.

- `knowledge/README.md` — Guía de la base de conocimiento.
  - Temario: Estructura actual; Formato de FAQs (JSON); Cómo extender la base; Buenas prácticas; Validación rápida; Próximos pasos.

- `chatbots/README.md` — Estructura del directorio de variantes.
  - Temario: Portada y estructura sugerida de `chatbots/<id>/` (config, reglas, RAG por variante).

## Guías y notas adicionales

- `start.txt` — Inicio rápido del Chatbot Municipal.
  - Temario: Preparación del entorno; Ejecución manual; Ejecución automatizada; (Opcional) Usar un LLM local.

- `README_ALTERNATIVO.txt` — Guía rápida para la variante MAR2 (modo libre).
  - Temario: Requisitos básicos; Iniciar API; Probar MAR2 por CLI (`channel="mar2"`); Usar el frontend MAR2 en navegador.

- `contexto.txt` — Resumen de cambios y estado del portal de chatbots.
  - Temario: Resumen (estado actual); Archivos añadidos/modificados; Ejecución rápida; Portal y variantes.

- `lanzamiento.txt` — Atajos de ejecución (dos comandos: API y servidor estático del frontend).
  - Temario: Comandos de arranque para desarrollo.

- `parametrizacion de bots.txt` — Parámetros y persistencia por bot (municipal, mar2).
  - Temario: Alcance y persistencia; Endpoints (`GET/PUT/POST reset`); Generación (temperature, top-p, max tokens) con rangos y sugerencias; Consejos rápidos por variante; Comportamiento (usar reglas/RAG); Menú de sugerencias; Botones del modal (guardar/restablecer/cancelar); Valores estándar por variante; Aplicación técnica (límites y enforcement en backend); Notas útiles.

## Guías in-code (comentarios de referencia)

- `services/orchestrator/intent_classifier.py` — Uso, parametrización, impacto y presets de intents (al final del archivo).
- `services/orchestrator/service.py` — Orquestador: flujo Reglas → RAG → LLM, pre_prompts, toggles y puntos de extensión.
- `services/orchestrator/rule_engine.py` — Motor de reglas: definición, matching, orden e impacto en latencia.
- `services/orchestrator/rag.py` — RAG ligero: uso, threshold, dataset JSON y migración a vector store.
- `services/chatbots/models.py` — Settings por bot: esquema, IO a `chatbots/<id>/settings.json`, defaults y ejemplos.
- `services/chatbots/router.py` — API de settings: ejemplos `curl` y consideraciones (persistencia/CORS).
- `services/orchestrator/router.py` — API de chat: contrato de `POST /chat/message`, ejemplo y notas.
- `services/llm_adapter/client.py` — Cliente LLM: uso, variables de entorno, placeholder y logging.
- `services/llm_adapter/settings.py` — Settings del LLM: variables soportadas y fuentes (.env/env).
- `services/api/main.py` — FastAPI/CORS: routers habilitados, `WEBCHATBOT_ALLOWED_ORIGINS`, ejecución local.
- `frontend/portal.js` — Portal: endpoints de configuración, `API_BASE_URL` y consejos.
- `frontend/app.js` — Cliente Municipal: comportamiento, `API_BASE_URL`, interacción con settings.
- `frontend/app_mar2.js` — Cliente MAR2: modo libre, `API_BASE_URL` y recomendaciones.

## Referencias técnicas y scripts

- `scripts/export_webchatbot_env.sh` — Exporta variables de entorno, añade el repo al `PYTHONPATH` y autodetecta un modelo `.gguf` en `modelos/` si existe.
- `scripts/check_host_readiness.py` — Diagnóstico del host (recursos, puertos, firewall, binarios) antes de exponer el servicio.
- `scripts/tune_low_latency.sh` — Inspección y ajuste opcional de latencia (preempción dinámica, CPU governor, BBR/fq). Incluye modo lectura y `--apply` para aplicar cambios con `sudo`.

## Archivos de requisitos

- `requirements.txt` — Dependencias mínimas.
- `requirements/dev.txt` — Dependencias de desarrollo y pruebas.
- `requirements/rag.txt` — Extras para RAG/LLM/observabilidad.
- `requirements-nlp.txt` — Requisitos de NLP (usar en entorno separado si hay conflicto de versiones).

## Presentaciones

- `rev_001.pptx` — Presentación (borrador) del proyecto.

## Cómo mantener este índice

- Añadí nuevas entradas al crear documentos en `docs/`, `frontend/`, `portal/`, `knowledge/` o la raíz.
- Incluí siempre: ubicación, propósito y temario (encabezados principales o resumen temático si es un `.txt`).
- Evitá listar documentación de paquetes externos del entorno virtual (`lib/`).
