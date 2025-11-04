#!/usr/bin/env python3
"""Verifica si la máquina está lista para exponer el webchatbot hacia Internet."""

from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import gzip


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class CheckResult:
    name: str
    status: str
    details: str | None = None

    def format(self) -> str:
        base = f"- {self.name}: {self.status}"
        if self.details:
            return f"{base}\n    {self.details}"
        return base


def run_command(cmd: Iterable[str]) -> tuple[int | None, str]:
    """Ejecuta un comando y devuelve (exit_code, salida)."""

    try:
        completed = subprocess.run(
            list(cmd),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except FileNotFoundError:
        return None, "comando inexistente"
    return completed.returncode, completed.stdout.strip()


def detect_default_model_path() -> Path | None:
    """Busca la ruta por defecto del modelo en el script de entorno."""

    env_script = PROJECT_ROOT / "scripts" / "export_webchatbot_env.sh"
    if not env_script.exists():
        return None
    text = env_script.read_text(encoding="utf-8", errors="ignore")
    match = re.search(
        r"WEBCHATBOT_DEFAULT_LLM_MODEL_PATH:=([^}\"\n]+)", text
    )
    if not match:
        return None
    return Path(match.group(1)).expanduser()


def describe_model_path() -> CheckResult:
    env_model = os.environ.get("LLM_MODEL_PATH")
    env_default = os.environ.get("WEBCHATBOT_DEFAULT_LLM_MODEL_PATH")
    fallback = detect_default_model_path()

    chosen = env_model or env_default or fallback
    if not chosen:
        return CheckResult(
            "Ruta modelo LLM",
            "SIN DEFINIR",
            "Definí LLM_MODEL_PATH o ajustá scripts/export_webchatbot_env.sh",
        )

    path = Path(chosen).expanduser()
    if not path.exists():
        return CheckResult(
            "Ruta modelo LLM",
            "NO ENCONTRADA",
            f"Esperado en {path}. Ejecutá el script de entorno o descargá el modelo.",
        )

    size_gb = path.stat().st_size / (1024**3)
    return CheckResult(
        "Ruta modelo LLM",
        "OK",
        f"{path} (≈ {size_gb:.2f} GiB)",
    )


def describe_python_runtime() -> list[CheckResult]:
    results: list[CheckResult] = []
    results.append(
        CheckResult("Python", "OK", f"Ejecutable: {sys.executable} ({platform.python_version()})")
    )

    for module in ("fastapi", "uvicorn", "httpx"):
        status = "OK"
        detail: str | None = None
        try:
            __import__(module)
        except ImportError as exc:  # pragma: no cover - depende del entorno
            status = "FALTA"
            detail = str(exc)
        results.append(CheckResult(f"Paquete {module}", status, detail))

    for module in ("llama_cpp",):
        try:
            __import__(module)
        except ImportError:
            results.append(
                CheckResult(
                    f"Paquete opcional {module}",
                    "NO DISPONIBLE",
                    "Instalalo si vas a servir respuestas LLM locales (make install-rag)",
                )
            )
        else:
            results.append(CheckResult(f"Paquete opcional {module}", "OK"))

    return results


def describe_system_resources() -> list[CheckResult]:
    results: list[CheckResult] = []
    cpu_count = os.cpu_count() or 0
    results.append(CheckResult("CPU", "OK", f"Núcleos detectados: {cpu_count}"))

    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        total_kib = 0.0
        available_kib = 0.0
        with meminfo.open("r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                if line.startswith("MemTotal:"):
                    total_kib = float(line.split()[1])
                if line.startswith("MemAvailable:"):
                    available_kib = float(line.split()[1])
        results.append(
            CheckResult(
                "Memoria RAM",
                "OK",
                f"Total ≈ {total_kib/1024/1024:.2f} GiB | Libre ≈ {available_kib/1024/1024:.2f} GiB",
            )
        )
    else:
        results.append(CheckResult("Memoria RAM", "DESCONOCIDO", "/proc/meminfo no disponible"))

    usage = shutil.disk_usage(PROJECT_ROOT)
    results.append(
        CheckResult(
            "Disco en raíz del proyecto",
            "OK",
            f"Libre ≈ {usage.free/1024/1024/1024:.2f} GiB de {usage.total/1024/1024/1024:.2f} GiB",
        )
    )

    return results


def describe_network(skip_public_ip: bool) -> list[CheckResult]:
    results: list[CheckResult] = []

    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        local_ip = "(no resuelve)"
    results.append(CheckResult("Hostname", "OK", f"{hostname} → {local_ip}"))

    if shutil.which("ip"):
        code, output = run_command(["ip", "-4", "addr", "show", "scope", "global"])
        status = "OK" if code == 0 else "ERROR"
        if output and "Operation not permitted" in output:
            status = "WARN"
        details = output if output else None
        results.append(CheckResult("Direcciones IPv4", status, details))
    elif shutil.which("ifconfig"):
        _, output = run_command(["ifconfig"])
        results.append(CheckResult("Interfaces", "DETECTADO", output))
    else:
        results.append(CheckResult("Interfaces", "NO DISPONIBLE", "Instalá iproute2 o net-tools"))

    if not skip_public_ip and shutil.which("curl"):
        code, output = run_command(["curl", "-fsS", "https://ifconfig.me"])
        if code == 0 and output:
            results.append(CheckResult("IP pública", "OK", output))
        else:
            results.append(
                CheckResult(
                    "IP pública",
                    "NO DISPONIBLE",
                    "No se pudo consultar ifconfig.me (verificá firewall o conectividad saliente)",
                )
            )
    elif not skip_public_ip:
        results.append(CheckResult("IP pública", "NO DISPONIBLE", "Instalá curl o usa --skip-public-ip"))

    if shutil.which("ss"):
        code, output = run_command(["ss", "-tuln"])
        status = "OK" if code == 0 else "ERROR"
        if output and "Operation not permitted" in output:
            status = "WARN"
        results.append(CheckResult("Puertos en escucha", status, output))
    elif shutil.which("netstat"):
        _, output = run_command(["netstat", "-tuln"])
        results.append(CheckResult("Puertos en escucha", "DETECTADO", output))
    else:
        results.append(CheckResult("Puertos en escucha", "NO DISPONIBLE", "Instalá ss o netstat"))

    if shutil.which("ufw"):
        code, output = run_command(["ufw", "status"])
        if code == 0:
            results.append(CheckResult("Firewall (ufw)", "OK", output))
        else:
            status = "ERROR"
            if output and "root" in output.lower():
                status = "WARN"
            results.append(CheckResult("Firewall (ufw)", status, output))
    else:
        results.append(CheckResult("Firewall (ufw)", "NO INSTALADO", "Considerá habilitar ufw o firewall equivalente"))

    return results


def describe_services() -> list[CheckResult]:
    results: list[CheckResult] = []

    for command in ("tmux", "systemctl", "fail2ban-client"):
        location = shutil.which(command)
        status = "OK" if location else "NO"
        detail = location or "Instalalo si forma parte de tu estrategia (ej. supervisión, tmux, fail2ban)."
        results.append(CheckResult(f"Comando {command}", status, detail))

    env_script = PROJECT_ROOT / "scripts" / "export_webchatbot_env.sh"
    if env_script.exists():
        results.append(CheckResult("Script de entorno", "OK", str(env_script)))
    else:
        results.append(CheckResult("Script de entorno", "FALTA", "No se encontró export_webchatbot_env.sh"))

    start_script = PROJECT_ROOT / "start.sh"
    if start_script.exists():
        results.append(CheckResult("start.sh", "OK", "Usalo como referencia para procesos supervisados"))
    else:
        results.append(CheckResult("start.sh", "FALTA", "Considerá crear un script de arranque"))

    return results


def describe_kernel_preemption() -> list[CheckResult]:
    results: list[CheckResult] = []

    # Runtime preemption mode (requires debugfs on some kernels)
    runtime_mode: str | None = None
    for p in (Path("/sys/kernel/debug/sched/preempt"), Path("/sys/kernel/sched/preempt")):
        try:
            if p.exists():
                runtime_mode = p.read_text(encoding="utf-8", errors="ignore").strip()
                break
        except Exception:
            pass
    if runtime_mode:
        results.append(CheckResult("Preempción (runtime)", "OK", runtime_mode))
    else:
        results.append(
            CheckResult(
                "Preempción (runtime)",
                "DESCONOCIDO",
                "No se pudo leer /sys/.../sched/preempt (montá debugfs o requiere privilegios)",
            )
        )

    # Kernel config (CONFIG_PREEMPT / CONFIG_PREEMPT_DYNAMIC)
    uname_rel = platform.release()
    cfg_file = Path(f"/boot/config-{uname_rel}")
    config_text: str | None = None
    if cfg_file.exists():
        try:
            config_text = cfg_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            config_text = None
    elif Path("/proc/config.gz").exists():
        try:
            with gzip.open("/proc/config.gz", "rt", encoding="utf-8") as gz:
                config_text = gz.read()
        except Exception:
            config_text = None

    if config_text:
        flags = []
        for key in ("CONFIG_PREEMPT_NONE", "CONFIG_PREEMPT_VOLUNTARY", "CONFIG_PREEMPT", "CONFIG_PREEMPT_DYNAMIC"):
            # Collect raw lines like: CONFIG_PREEMPT=y or # CONFIG_PREEMPT_NONE is not set
            for line in config_text.splitlines():
                if line.startswith(key):
                    flags.append(line.strip())
                    break
        detail = "; ".join(flags) if flags else None
        results.append(CheckResult("Kernel PREEMPT flags", "OK", detail))
        if "CONFIG_PREEMPT_DYNAMIC=y" in (config_text or ""):
            results.append(
                CheckResult(
                    "Sugerencia PREEMPT",
                    "INFO",
                    "Podés alternar runtime (full/voluntary/none) si /sys/.../sched/preempt está disponible, o usar 'preempt=full' en GRUB",
                )
            )
    else:
        results.append(CheckResult("Kernel PREEMPT flags", "DESCONOCIDO", "No encontré /boot/config-* ni /proc/config.gz"))

    return results


def describe_cpu_governor() -> list[CheckResult]:
    results: list[CheckResult] = []
    base = Path("/sys/devices/system/cpu")
    govs: dict[str, int] = {}
    if base.exists():
        for cpu_dir in sorted(base.glob("cpu[0-9]*")):
            gfile = cpu_dir / "cpufreq" / "scaling_governor"
            if gfile.exists():
                try:
                    g = gfile.read_text(encoding="utf-8", errors="ignore").strip()
                    govs[g] = govs.get(g, 0) + 1
                except Exception:
                    pass
    if govs:
        detail = ", ".join(f"{k}: {v}" for k, v in govs.items())
        results.append(CheckResult("CPU governor(s)", "OK", detail))
    else:
        results.append(CheckResult("CPU governor(s)", "DESCONOCIDO", "cpufreq no disponible"))
    return results


def describe_net_stack_extra() -> list[CheckResult]:
    results: list[CheckResult] = []
    if shutil.which("sysctl"):
        _, cc = run_command(["sysctl", "-n", "net.ipv4.tcp_congestion_control"])
        _, qd = run_command(["sysctl", "-n", "net.core.default_qdisc"])
        _, sc = run_command(["sysctl", "-n", "net.core.somaxconn"])
        results.append(CheckResult("TCP cc", "OK", cc or "(n/d)"))
        results.append(CheckResult("qdisc", "OK", qd or "(n/d)"))
        results.append(CheckResult("somaxconn", "OK", sc or "(n/d)"))
    else:
        results.append(CheckResult("Stack TCP", "DESCONOCIDO", "sysctl no disponible"))
    return results


def print_section(title: str, results: list[CheckResult]) -> None:
    print(f"\n=== {title} ===")
    for item in results:
        print(item.format())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-public-ip",
        action="store_true",
        help="Omite la consulta a ifconfig.me (útil si no hay salida a Internet)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("Chequeo de preparación para exponer webchatbot")
    print(f"Proyecto: {PROJECT_ROOT}")
    print(f"Sistema: {platform.platform()} ({platform.machine()})")

    print_section("Runtime Python", describe_python_runtime())
    print_section("Modelo LLM", [describe_model_path()])
    print_section("Recursos del sistema", describe_system_resources())
    print_section("Kernel/Preempción", describe_kernel_preemption())
    print_section("CPU Governor", describe_cpu_governor())
    print_section("Red", describe_network(skip_public_ip=args.skip_public_ip))
    print_section("Red (stack)", describe_net_stack_extra())
    print_section("Servicios y herramientas", describe_services())

    print("\nRevisión completa. Analizá los ítems marcados como FALTA/NO/ERROR.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
