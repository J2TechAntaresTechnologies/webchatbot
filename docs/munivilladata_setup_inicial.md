# Setup inicial recomendado (Munivilla)

Documento breve con valores sugeridos para arrancar y cómo aplicarlos.

## Parámetros sugeridos (Municipal)
- generation: { temperature: 0.7, top_p: 0.9, max_tokens: 200 }
- features: { use_rules: true, use_rag: true, use_generic_no_match: true, enable_default_rules: true }
- rag_threshold: 0.28
- pre_prompts:
  - "Responde con frases cortas y claras; listas con viñetas cuando enumeres."
  - "Prefiere fuentes oficiales y menciona el canal/área responsable cuando aplique."
  - "Ante emergencias: indicar 911 (Policía), 107 (Hospital), 100 (Bomberos)."
- menu_suggestions: ver `docs/munivilladata_propuesta_menu.md` (sección Chips).
- rules: agregar acciones directas (turnos, proveedores, emergencias, discapacidad, punto violeta, consumos).

## Aplicación rápida (vía Portal)
1) Levantar API y frontend: `./start.sh` o `./start_noverbose.sh`.
2) Abrir `http://localhost:5173` → botón “Parámetros” en “Chatbot Municipal”.
3) Cargar los valores anteriores y Guardar.

## Aplicación por API (curl)
```bash
curl -sS -X PUT \
  http://127.0.0.1:8000/chatbots/municipal/settings \
  -H 'Content-Type: application/json' \
  -d '{
    "generation": {"temperature": 0.7, "top_p": 0.9, "max_tokens": 200},
    "features": {"use_rules": true, "use_rag": true, "use_generic_no_match": true, "enable_default_rules": true},
    "rag_threshold": 0.28,
    "pre_prompts": [
      "Responde con frases cortas y claras; listas con viñetas cuando enumeres.",
      "Prefiere fuentes oficiales y menciona el canal/área responsable cuando aplique.",
      "Ante emergencias: indicar 911 (Policía), 107 (Hospital), 100 (Bomberos)."
    ]
  }'
```

## Notas
- Editar/añadir entradas RAG en `knowledge/faqs/municipal_faqs.json` y reiniciar la API para reindexar.
- Mantener reglas y chips alineados con las prioridades de servicio.

