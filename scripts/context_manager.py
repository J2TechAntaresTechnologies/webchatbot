#!/usr/bin/env python3
"""Gestor de contexto del proyecto (leer/guardar resumen de cambios).

Uso:
  - Mostrar todo el contexto:  ./bin/python scripts/context_manager.py show
  - Mostrar resumen breve:     ./bin/python scripts/context_manager.py show --brief
  - Guardar entrada automática:./bin/python scripts/context_manager.py save --auto [--note "mensaje"]
  - Guardar con nota manual:  ./bin/python scripts/context_manager.py save --note "mensaje"

El archivo de contexto se guarda en 'contexto.txt' en la raíz del proyecto.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTEXT_FILE = PROJECT_ROOT / "contexto.txt"


def _run(cmd: Sequence[str]) -> tuple[int, str]:
    try:
        cp = subprocess.run(list(cmd), check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return cp.returncode, cp.stdout.strip()
    except FileNotFoundError:
        return 127, ""


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")


def _local_now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S %z")


def _detect_git() -> dict[str, str | None]:
    code, branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    code2, rev = _run(["git", "rev-parse", "--short", "HEAD"])
    if code != 0 or code2 != 0:
        return {"branch": None, "rev": None}
    return {"branch": branch, "rev": rev}


def _recent_files(limit: int = 10) -> list[str]:
    ignore_dirs = {"bin", "lib", "lib64", "include", "share", "__pycache__", ".pytest_cache", ".git"}
    candidates: list[tuple[float, Path]] = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # filtrar directorios ignorados
        parts = set(Path(root).relative_to(PROJECT_ROOT).parts)
        if parts & ignore_dirs:
            # si cualquier parte está en los ignorados, saltar
            continue
        for f in files:
            p = Path(root) / f
            try:
                mtime = p.stat().st_mtime
            except FileNotFoundError:
                continue
            candidates.append((mtime, p))
    candidates.sort(key=lambda x: x[0], reverse=True)
    return [str(p.relative_to(PROJECT_ROOT)) for _, p in candidates[:limit]]


def _list_chatbots() -> list[dict[str, str]]:
    base = PROJECT_ROOT / "chatbots"
    if not base.exists():
        return []
    items: list[dict[str, str]] = []
    for child in sorted(base.iterdir()):
        cfg = child / "config.json"
        if cfg.exists():
            try:
                data = json.loads(cfg.read_text(encoding="utf-8"))
            except Exception:
                continue
            items.append({
                "id": str(data.get("id") or child.name),
                "name": str(data.get("name") or child.name),
                "channel": str(data.get("channel") or "web"),
                "page": str(data.get("frontend_page") or ""),
            })
    return items


def _compose_auto_entry(note: str | None = None) -> str:
    git = _detect_git()
    bots = _list_chatbots()
    files = _recent_files()
    py = sys.version.split()[0]
    py_exec = sys.executable
    system = platform.platform()
    lines: list[str] = []
    lines.append(f"\n=== Entrada contexto — { _utc_now() } (local { _local_now() }) ===")
    if note:
        lines.append(f"Nota: {note}")
    if git["branch"] or git["rev"]:
        lines.append(f"Git: {git['branch']} @ {git['rev']}")
    lines.append(f"Python: {py} ({py_exec}) | Sistema: {system}")
    if bots:
        readable = ", ".join(f"{b['id']}[{b['channel']}]→{b['page']}" for b in bots)
        lines.append(f"Chatbots registrados: {len(bots)} → {readable}")
    if files:
        lines.append("Últimos archivos modificados:")
        for rel in files:
            lines.append(f" - {rel}")
    lines.append("=== Fin de entrada ===\n")
    return "\n".join(lines)


def cmd_show(brief: bool) -> int:
    if not CONTEXT_FILE.exists():
        print("[INFO] No existe 'contexto.txt'. Guardá una entrada con el subcomando 'save'.")
        return 0
    text = CONTEXT_FILE.read_text(encoding="utf-8", errors="ignore")
    if not brief:
        print(text)
        return 0
    # En modo breve, mostrar última entrada si existen separadores, sino tail de 40 líneas.
    parts = [p for p in text.split("=== Entrada contexto") if p.strip()]
    if parts:
        print("=== Entrada contexto" + parts[-1])
    else:
        lines = text.splitlines()[-40:]
        print("\n".join(lines))
    return 0


def cmd_save(auto: bool, note: str | None) -> int:
    CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
    if auto:
        entry = _compose_auto_entry(note)
    else:
        when = f"{_utc_now()} (local {_local_now()})"
        header = f"\n=== Entrada contexto — {when} ===\n"
        entry = header + (f"Nota: {note}\n" if note else "") + "=== Fin de entrada ===\n"
    with CONTEXT_FILE.open("a", encoding="utf-8") as fh:
        fh.write(entry)
    print("[OK] Contexto guardado en", CONTEXT_FILE)
    return 0


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_show = sub.add_parser("show", help="Muestra el archivo de contexto")
    p_show.add_argument("--brief", action="store_true", help="Sólo la última entrada o último bloque")

    p_save = sub.add_parser("save", help="Agrega una entrada al archivo de contexto")
    p_save.add_argument("--auto", action="store_true", help="Genera entrada automática con metadatos")
    p_save.add_argument("--note", type=str, default=None, help="Nota o comentario a incluir")

    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if args.cmd == "show":
        return cmd_show(brief=getattr(args, "brief", False))
    if args.cmd == "save":
        return cmd_save(auto=getattr(args, "auto", False), note=getattr(args, "note", None))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

