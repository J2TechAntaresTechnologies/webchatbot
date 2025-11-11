# Integración de Datos Munivilla: Reglas (FAQ), RAG y LLM

Este documento explica cómo integrar los contenidos de `00relevamientos_j2/munivilladata/` al bot, decidiendo qué va como “respuesta rápida” (reglas), qué va a la base de conocimiento (RAG) y qué dejar al LLM, con ejemplos concretos y rutas del repo.

## Criterios de decisión
- Reglas (FAQ/fallback):
  - Respuestas cortas, inequívocas, orientadas a acción (teléfonos, links, cómo sacar turno, números de emergencia).
  - Se configuran por bot y responden al instante si hay match de keywords.
  - Lugar: `chatbots/<id>/settings.json > rules[]`.
- RAG (FAQs enriquecidas):
  - Preguntas que requieren párrafo breve con contexto/categorización (centros, campañas, actividades, trámites explicados).
  - Se buscan por similitud léxica con umbral configurable.
  - Lugar: `knowledge/faqs/municipal_faqs.json` (JSONC; admite comentarios).
- LLM (fallback):
  - Consultas abiertas/no cubiertas o redacciones fuera de alcance del dataset.
  - Estilo guiado por `pre_prompts` del bot; se invoca cuando no hay match en reglas/RAG o cuando el canal es “mar2”.

## Ejemplos de integración
### 1) Reglas (respuestas rápidas)
Lugar: `chatbots/municipal/settings.json > rules[]`

```json
{
  "enabled": true,
  "keywords": ["emergenc", "polic", "bombero", "accident", "hospital"],
  "response": "Emergencias: Policía 911, Hospital 107, Bomberos 100. Tel. municipal: 435500.",
  "source": "fallback"
}
```

```json
{
  "enabled": true,
  "keywords": ["turno", "licenc", "conduc"],
  "response": "Solicitá o reprogramá tu turno de Licencia de Conducir en https://<enlace-oficial>.",
  "source": "faq"
}
```

```json
{
  "enabled": true,
  "keywords": ["proveedor", "inscrip", "compra"],
  "response": "La inscripción de proveedores se realiza en https://<enlace>. Tené a mano CUIT y documentación.",
  "source": "faq"
}
```

Sugerencias adicionales: “Punto Violeta”, “Consumos problemáticos”, “Certificado de Discapacidad”, “Obras privadas”.

### 2) RAG (FAQs enriquecidas)
Lugar: `knowledge/faqs/municipal_faqs.json` (JSONC). Se admiten comentarios.

```jsonc
[
  {
    "uid": "vc-001",
    "question": "¿Qué es y dónde está el Punto Violeta?",
    "answer": "Punto Violeta brinda escucha y contención en temas de género. Consultá ubicación/horarios en el sitio oficial o en Atención Ciudadana.",
    "tags": ["genero", "violeta", "igualdad", "apoyo"]
  },
  {
    "uid": "vc-002",
    "question": "¿Dónde pedir ayuda por consumos problemáticos?",
    "answer": "El municipio ofrece orientación y acompañamiento profesional. Contacto en [área], o solicitá turno en [canal].",
    "tags": ["consumo", "adiccion", "salud", "apoyo"]
  },
  {
    "uid": "vc-003",
    "question": "¿Cómo tramitar el Certificado de Discapacidad?",
    "answer": "Requisitos, turnos y evaluación en [enlace]. Presentá documentación médica actualizada.",
    "tags": ["certificado", "discapacidad", "tramite"]
  }
]
```

Tras editar, reiniciar la API para reindexar (carga en `services/orchestrator/rag.py`).

### 3) Clasificador de intents (opcional)
Lugar: `services/orchestrator/intent_classifier.py`.
Agregar patrones para encaminar más consultas a RAG:

```python
from services.orchestrator.intent_classifier import IntentPattern

# Ejemplos a agregar al preset por defecto
IntentPattern(intent="rag", keywords=("licenc", "conduc"), confidence=0.65)
IntentPattern(intent="rag", keywords=("proveedor", "inscrip"), confidence=0.65)
IntentPattern(intent="rag", keywords=("discap", "certific"), confidence=0.65)
IntentPattern(intent="rag", keywords=("genero", "violeta"), confidence=0.65)
IntentPattern(intent="rag", keywords=("dengue",), confidence=0.65)
```

### 4) Pre-prompts y chips
- Lugar (ambos): `chatbots/municipal/settings.json`.
- `pre_prompts`: listas de estilo/políticas (se anteponen cuando se llama al LLM).
- `menu_suggestions`: chips que el cliente municipal muestra como atajos.

## Dónde impacta cada cambio
- Reglas: responden si el intent clasificado es `faq` o `smalltalk` y hay match (con prioridad a reglas custom del bot). Ver `services/orchestrator/service.py`.
- RAG: responde si el intent es `rag` y el score ≥ `rag_threshold`. Si no supera, continúa flujo.
- LLM: responde cuando no aplican reglas/RAG o en canal “mar2”. El estilo se condiciona con `pre_prompts`.

## Buenas prácticas
- Reglas: usar stems ("licenc", "conduc") y 2–4 keywords por tema para reducir falsos positivos.
- RAG: mantener `answer` breve (< 800 chars), tags en minúscula sin tildes, uid único.
- Clasificador: colocar patrones específicos antes que genéricos; revisar con ejemplos reales.
- Validación: probar consultas de regresión (pagos, turnos, proveedores, discapacidad, dengue, juventud) tras cada cambio.

