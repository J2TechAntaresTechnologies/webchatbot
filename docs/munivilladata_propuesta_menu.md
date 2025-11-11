# Propuesta de Menú, Conversación y Parámetros (Munivilla)

Este documento resume una propuesta concreta de navegación/conversación para el bot municipal, basada en los contenidos de `00relevamientos_j2/munivilladata/` y en las capacidades actuales del proyecto.

## Objetivos
- Facilitar acceso rápido a servicios clave con “respuestas rápidas” (reglas FAQ/fallback).
- Cubrir información más textual mediante RAG (FAQs enriquecidas) con umbral controlado.
- Mantener una UX clara con chips de menú y respuestas breves.

## Menú de alto nivel
- Bienestar y Salud
  - Centros: CIC, AMSA, Consumos problemáticos, Género e Igualdad, Punto Violeta, Certificado de Discapacidad
  - Campañas: “Chau! Dengue”
- Educación y Juventud
  - Deporte y Juventud, Educación (Congreso CER), Fondo de Asistencia Educativa, Economía Social
- Trámites y Gestiones
  - Trámites Online, Turnos Online (Licencia de Conducir), Inscripción de Proveedores
- Cultura, Turismo y Ambiente
  - Cultura (agenda), Turismo (atractivos), Ambiente (Villa Más Limpia)
- Desarrollo Urbano y Comercio
  - Obras Privadas, Planificación, Comercio
- Información y Contacto
  - Noticias y redes, Emergencias (911/107/100), Teléfono municipal (435500)

## Chips de sugerencias (Portal/cliente Municipal)
Sugeridos para `chatbots/municipal/settings.json > menu_suggestions`:
- Trámites online → "¿Qué trámites puedo hacer online?"
- Turnos licencia de conducir → "Quiero sacar un turno para licencia de conducir"
- Inscripción de proveedores → "¿Cómo me inscribo como proveedor municipal?"
- Punto Violeta → "¿Qué es el Punto Violeta y dónde está?"
- Consumos problemáticos → "Necesito ayuda por consumos problemáticos"
- Certificado de discapacidad → "¿Cómo tramito el Certificado de Discapacidad?"
- Cultura y agenda → "¿Qué actividades culturales hay este mes?"
- Turismo → "¿Qué atractivos turísticos tiene la ciudad?"
- Ambiente (Villa Más Limpia) → "¿Cómo es la separación y recolección?"
- Economía social → "¿Qué apoyo brinda Economía Social?"
- Obras privadas → "¿Cómo son los trámites de obras privadas?"
- Contacto y emergencias → "Necesito números de contacto y emergencias"

## Parámetros recomendados
- Municipal (guiado)
  - generation: temperature 0.65–0.75, top_p 0.85–0.9, max_tokens 180–220
  - features: use_rules=true, use_rag=true, use_generic_no_match=true, enable_default_rules=true
  - rag_threshold: 0.28 (ajustar 0.25–0.35 según recall/precisión)
  - pre_prompts (estilo/seguridad):
    - "Responde con frases cortas y claras; listas con viñetas cuando enumeres."
    - "Prefiere fuentes oficiales y menciona el canal/área responsable cuando aplique."
    - "Ante emergencias: indicar 911 (Policía), 107 (Hospital), 100 (Bomberos)."
    - "Si la consulta excede el alcance del municipio, indicá el organismo competente."
- MAR2 (modo libre)
  - generation: temperature 0.9–1.1, top_p 0.95–1.0, max_tokens 256–300
  - features: use_rules=false, use_rag=false, use_generic_no_match=false

## Árbol ASCII (Navegación sugerida)
- Inicio
  - Bienestar y Salud
    - Centros: CIC
    - Centros: AMSA
    - Consumos problemáticos
    - Género e Igualdad
    - Punto Violeta
    - Certificado de Discapacidad
    - Campañas: Chau! Dengue
  - Educación y Juventud
    - Deporte y Juventud
    - Educación (Congreso CER)
    - Fondo de Asistencia Educativa
    - Economía Social
  - Trámites y Gestiones
    - Trámites Online
    - Turnos Online (Licencia de Conducir)
    - Inscripción de Proveedores
  - Cultura, Turismo y Ambiente
    - Cultura (Agenda)
    - Turismo (Atractivos)
    - Ambiente (Villa Más Limpia)
  - Desarrollo Urbano y Comercio
    - Obras Privadas
    - Planificación
    - Comercio
  - Información y Contacto
    - Noticias y Redes
    - Emergencias (911 / 107 / 100)
    - Teléfono municipal (435500)

