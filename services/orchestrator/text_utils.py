"""Utilidades comunes para procesamiento de texto en el orquestador."""

from __future__ import annotations

import unicodedata


def normalize_text(text: str) -> str:
    """Normaliza texto para comparación básica sin tildes ni mayúsculas."""
    lowered = text.lower()
    normalized = unicodedata.normalize("NFD", lowered)
    return "".join(char for char in normalized if not unicodedata.combining(char))
