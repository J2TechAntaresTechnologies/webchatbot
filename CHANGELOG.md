# Changelog

All notable changes to this project will be documented in this file.

## v0.3.0 - 2025-11-11

Frontend
- Portal: nuevo toggle en Configuración de tema “Mostrar modo libre (MAR2) en el portal”. Permite ocultar/mostrar la tarjeta de MAR2 en la pantalla principal. Preferencia persistida en localStorage (`webchatbot_show_mar2`).
- Docs: README de frontend actualizado con la nueva opción y nota sobre que localStorage es por origen (host/puerto).

Scripts
- start_noverbose.sh: variante de arranque que reduce el ruido de logs sin modificar el código.
  - Uvicorn con `--log-level warning`.
  - Backend llama.cpp/ggml con `GGML_LOG_LEVEL=ERROR` y `LLAMA_LOG_LEVEL=ERROR`.

Docs
- README (raíz): se documenta `start_noverbose.sh`, variables de log de llama.cpp y nota sobre preferencias por origen.
- docs/manual_aprendizaje.md y docs/operacion_configuracion_chatbots.md: se incorporan notas de ejecución silenciosa y visibilidad de MAR2 desde el Portal.

Misc
- Ajustes menores de redacción y consistencia en documentación.

---

Formato de versionado: Semántico informal (MAJOR.MINOR.PATCH). Cambios funcionales visibles en frontend o scripts se reflejan con MINOR.
