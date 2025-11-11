"""
RAG Ligero por Similitud Léxica
===============================

Resumen
-------
Este módulo implementa un componente RAG (Retrieval-Augmented Generation)
ligero que recupera respuestas desde una base de conocimiento embebida en
memoria usando similitud de coseno sobre representaciones bag-of-words
normalizadas. Está pensado como baseline simple, sin dependencias externas de
vector stores, para dominios acotados con preguntas frecuentes.

Índice (Mapa del archivo)
-------------------------
1) Importaciones y utilidades
2) `KnowledgeEntry` (dataclass): esquema de la base de conocimiento
3) `SimpleRagResponder`: buscador RAG en memoria
   - `__init__`: vectoriza entradas (una sola vez); umbral de similitud
   - `search`: embebe consulta, compara y aplica umbral
   - `_embed`/`_embed_text`: bag-of-words con ponderación 1/len(tokens)
4) `load_default_entries`: carga JSON de `knowledge/faqs/municipal_faqs.json`
5) Helpers privados: `_tokenize`, `_cosine_similarity`
6) Guía de uso y parametrización (al final del archivo)

Cómo funciona
-------------
- Preprocesamiento: se normaliza texto (minúsculas, sin tildes) con
  `normalize_text` antes de tokenizar.
- Embeddings: representación tipo TF simple (cada token aporta 1/len(tokens)).
  Sin IDF, sin stemming, sin stopwords. Es intencionalmente simple.
- Similitud: coseno entre vectores dispersos (dict token→peso). Resultado en el
  rango [0, 1].
- Umbral: si la mejor similitud < `threshold`, no se devuelve respuesta (None).

Consideraciones y límites
-------------------------
- Umbral recomendado: 0.20–0.40 según calidad de datos. Valor por defecto: 0.28.
  Valores fuera de [0,1] no tienen sentido; mantener 0 ≤ threshold ≤ 1.
- Performance: O(N·V) por búsqueda (N entradas, V tokens comunes). Adecuado para
  cientos o pocos miles de entradas. Para más escala, migrar a un vector store.
- Calidad: al no usar IDF, términos muy frecuentes pueden influir más de lo
  deseado. Mejorar datos con tags específicos aumenta la señal.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from math import sqrt
from pathlib import Path
import re
from typing import Iterable, Sequence

from services.orchestrator.text_utils import normalize_text


@dataclass(frozen=True)
class KnowledgeEntry:
    """Entrada simple de la base de conocimiento.

    Campos
    - uid: identificador único de la entrada (string). Sin restricciones de
      formato, pero debe ser estable para trazabilidad.
    - question: texto de la pregunta canónica (string). Recomendada concisión
      y uso de vocabulario típico de usuarios.
    - answer: texto de la respuesta (string). Mantener actualizado y claro.
      Sin límites estrictos de longitud; recomendado < ~800 caracteres para
      buena UX.
    - tags: lista/tupla de etiquetas (Sequence[str]) que resumen conceptos
      relevantes. Útiles para mejorar recall en la similitud.
    """

    uid: str
    question: str
    answer: str
    tags: Sequence[str]


class SimpleRagResponder:
    """Busca respuestas en una base de conocimiento embebida en memoria.

    - Al inicializar, vectoriza todas las entradas una única vez (_vectors),
      lo que mejora el tiempo de consulta.
    - Usa similitud de coseno entre embeddings de consulta y entradas.
    - Aplica un umbral `threshold` para decidir si devuelve una respuesta.
    """

    def __init__(self, entries: Sequence[KnowledgeEntry], threshold: float = 0.28) -> None:
        # entries: colección de KnowledgeEntry a indexar en memoria.
        #   Tamaño sugerido: hasta unos miles para mantener consultas ágiles.
        # threshold: valor en [0,1] que define el mínimo de similitud de coseno
        #   aceptable para retornar una respuesta. Recomendado 0.20–0.40; por
        #   defecto 0.28. Valores menores aumentan recall y falsos positivos; valores
        #   mayores aumentan precision y el riesgo de no devolver resultados.
        self._entries = entries
        self._threshold = threshold
        # Precompute embeddings (bag-of-words normalizado) para cada entrada.
        self._vectors = [self._embed(entry) for entry in entries]

    async def search(self, message: str) -> str | None:
        """Busca la mejor respuesta para `message`.

        Flujo
        - Embebe la consulta en un vector disperso (token→peso TF).
        - Recorre todas las entradas y calcula similitud de coseno.
        - Selecciona el máximo; aplica umbral. Devuelve `answer` o None.

        Retorno
        - str | None: respuesta si supera threshold, si no, None.
        """
        # Embedding de la consulta (usa normalización y tokenización simple).
        query_vector = self._embed_text(message)
        if not query_vector:
            # Sin tokens → no hay señal para comparar.
            return None

        # Búsqueda de máximo (argmax) sobre todas las entradas.
        best_score = 0.0
        best_answer: str | None = None
        for entry, vector in zip(self._entries, self._vectors):
            score = _cosine_similarity(query_vector, vector)
            if score > best_score:
                best_score = score
                best_answer = entry.answer

        # Aplicación de umbral: rango esperado del score ∈ [0,1].
        if best_answer is None or best_score < self._threshold:
            return None
        return best_answer

    def _embed(self, entry: KnowledgeEntry) -> dict[str, float]:
        """Construye el vector de una entrada uniendo question + tags.

        - Concatenamos la pregunta con sus etiquetas para mejorar recall.
        - Salida: dict token→peso (float en [0,1]), suma aproximadamente 1.
        """
        text = " ".join([entry.question, *entry.tags])
        return self._embed_text(text)

    @staticmethod
    def _embed_text(text: str) -> dict[str, float]:
        """Convierte texto en un vector TF normalizado.

        - Tokenización: split por espacios tras `normalize_text` (minúsculas,
          sin tildes). No remueve stopwords.
        - Ponderación: cada token suma 1/len(tokens). Sin límites en cantidad
          de tokens, pero textos extremadamente largos diluyen pesos.
        """
        tokens = _tokenize(text)
        if not tokens:
            return {}
        total = float(len(tokens))
        vector: dict[str, float] = {}
        for token in tokens:
            vector[token] = vector.get(token, 0.0) + 1.0 / total
        return vector


def load_default_entries(path: Path | None = None) -> Sequence[KnowledgeEntry]:
    """Carga entradas de `knowledge/faqs/municipal_faqs.json`.

    Parámetros
    - path: ruta opcional a un JSON compatible. Si es None, usa la ruta por
      defecto relativa al repo. El archivo debe existir y contener una lista de
      objetos con campos: uid (str), question (str), answer (str), tags (list[str]).

    Retorno
    - list[KnowledgeEntry]: lista de entradas cargadas.

    Notas
    - Errores de E/S o formato JSON se propagan (FileNotFoundError, JSONDecodeError).
      El orquestador captura FileNotFoundError en el bootstrap.
    """

    # Ruta por defecto al dataset de FAQs municipal (puede personalizarse via `path`).
    base_path = path or Path(__file__).resolve().parents[2] / "knowledge" / "faqs" / "municipal_faqs.json"
    # Soporte de JSON con comentarios (JSONC):
    # Permitimos comentarios // ... y /* ... */ en el archivo para documentación inline.
    # Se eliminan antes de parsear con json.loads.
    raw_text = base_path.read_text(encoding="utf-8")
    cleaned = _strip_json_comments(raw_text)
    payload: Iterable[dict[str, object]] = json.loads(cleaned)
    entries: list[KnowledgeEntry] = []
    for item in payload:
        entries.append(
            KnowledgeEntry(
                uid=str(item.get("uid")),
                question=str(item.get("question")),
                answer=str(item.get("answer")),
                tags=tuple(str(tag) for tag in item.get("tags", [])),
            )
        )
    return entries


def load_text_dir_entries(text_dir: Path) -> Sequence[KnowledgeEntry]:
    """Carga entradas de texto desde un directorio plano (.txt) para usarlas como KB.

    Heurística simple:
    - Recorre archivos *.txt del directorio `text_dir`.
    - Divide en párrafos por líneas en blanco.
    - Crea una KnowledgeEntry por párrafo no vacío (≥ 160 caracteres aprox.).
    - question: primera oración o los primeros ~120 caracteres del párrafo.
    - answer: el párrafo completo (recortado).
    - tags: tokens derivados del nombre del archivo (sin extensión).

    Pensado para “munivilladata” y documentos curatoriales. No requiere editar
    el JSON principal y permite ampliar cobertura sin cambiar estructura.
    """
    entries: list[KnowledgeEntry] = []
    if not text_dir.exists() or not text_dir.is_dir():
        return entries
    for path in sorted(text_dir.glob("*.txt")):
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # Normalizar saltos y separar por párrafos
        blocks = [b.strip() for b in re.split(r"\n\s*\n+", raw) if b and b.strip()]
        # Tags desde el nombre del archivo
        stem = path.stem.lower()
        tags = tuple(t for t in re.split(r"[^a-z0-9]+", stem) if t)
        for i, para in enumerate(blocks):
            # Filtrar párrafos muy cortos (saludos, cabeceras)
            if len(para) < 160:
                continue
            # Pregunta/encabezado breve para indexar
            # Tomamos la primera oración o 120 caracteres
            m = re.split(r"(?<=[\.!?])\s+", para)
            head = m[0] if m else para
            question = head.strip()
            if len(question) > 120:
                question = question[:117].rstrip() + "…"
            uid = f"txt-{stem}-{i:03d}"
            entries.append(
                KnowledgeEntry(
                    uid=uid,
                    question=question,
                    answer=para.strip(),
                    tags=tags,
                )
            )
    return entries


def _tokenize(text: str) -> list[str]:
    """Tokeniza un texto normalizado en palabras separadas por espacio.

    - Aplica `normalize_text` (minúsculas, sin tildes) antes de dividir.
    - No elimina stopwords ni hace stemming. Para dominios con jerga estable,
      esto suele ser suficiente como baseline.
    """
    normalized = normalize_text(text)
    tokens = [token for token in normalized.split() if token]
    return tokens


def _cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Calcula similitud de coseno entre dos vectores dispersos.

    Rango
    - Devuelve valores en [0, 1] (no negativos porque los pesos son >= 0).

    Estabilidad numérica
    - Retorna 0.0 si alguno está vacío, si el numerador es 0, o si alguna norma
      es 0 para evitar divisiones inválidas.
    """
    if not vec_a or not vec_b:
        return 0.0

    common = set(vec_a).intersection(vec_b)
    numerator = sum(vec_a[token] * vec_b[token] for token in common)
    if numerator == 0:
        return 0.0

    norm_a = sqrt(sum(value * value for value in vec_a.values()))
    norm_b = sqrt(sum(value * value for value in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0

    return numerator / (norm_a * norm_b)


def _strip_json_comments(text: str) -> str:
    """Elimina comentarios tipo JSONC de una cadena JSON.

    Soporta:
    - Comentarios de línea: // ... (hasta fin de línea)
    - Comentarios de bloque: /* ... */ (multilínea)

    Conserva el contenido dentro de strings JSON ("...") incluyendo secuencias
    escapadas. No depende de librerías externas.
    """
    result: list[str] = []
    i = 0
    n = len(text)
    in_string = False
    escaped = False
    in_sl_comment = False
    in_ml_comment = False

    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""

        if in_sl_comment:
            if ch == "\n":
                in_sl_comment = False
                result.append(ch)
            i += 1
            continue

        if in_ml_comment:
            if ch == "*" and nxt == "/":
                in_ml_comment = False
                i += 2
            else:
                i += 1
            continue

        if in_string:
            result.append(ch)
            if escaped:
                # caracter escapado dentro de string
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        # Fuera de string y comentarios
        if ch == '"':
            in_string = True
            escaped = False
            result.append(ch)
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_sl_comment = True
            i += 2
            continue

        if ch == "/" and nxt == "*":
            in_ml_comment = True
            i += 2
            continue

        result.append(ch)
        i += 1

    return "".join(result)

# ================================================================
# Guía de uso, parametrización e impacto (RAG ligero)
# ================================================================
#
# ¿Qué hace?
# -----------
# Carga entradas de conocimiento (pregunta, respuesta, tags) desde JSON y
# aplica una similitud léxica simple (bag-of-words normalizada) para recuperar
# una respuesta si supera un umbral.
#
# Uso básico
# -----------
# from services.orchestrator.rag import load_default_entries, SimpleRagResponder
# entries = load_default_entries()  # knowledge/faqs/municipal_faqs.json
# rag = SimpleRagResponder(entries, threshold=0.28)
# reply = await rag.search("¿Dónde consulto la ordenanza de poda?")
# if reply is not None: ...
#
# Parametrización
# ---------------
# - threshold: elevarlo reduce falsos positivos (más precision, menos recall).
# - dataset: modificar/expandir knowledge/faqs/*.json con campos uid,question,answer,tags.
# - tokenización: se usa normalize_text() y conteo proporcional; términos en tags ayudan a recall.
#
# Impacto en el bot
# -----------------
# - Con use_rag=True, el orquestador consultará RAG cuando el intent sea "rag".
# - Buen dataset + tags relevantes mejoran precisión y reducen caídas al LLM.
#
# Escalamiento
# ------------
# - Para pasar a embeddings reales y vector store (Chroma/Qdrant), implementar un
#   conector que cumpla RagResponderProtocol (método async search) y usar attach_rag().
