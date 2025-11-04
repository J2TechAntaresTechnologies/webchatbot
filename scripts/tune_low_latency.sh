#!/usr/bin/env bash
# Helper para ajustar parámetros de baja latencia (opcional, requiere sudo para aplicar cambios).
# Uso:
#   ./scripts/tune_low_latency.sh            # sólo mostrar estado y sugerencias
#   ./scripts/tune_low_latency.sh --apply    # aplicar cambios sugeridos (solicitará sudo)
# Flags opcionales:
#   --preempt [full|voluntary|none]  # selecciona modo de preempción (si el kernel soporta CONFIG_PREEMPT_DYNAMIC)
#   --governor [performance|schedutil|powersave]  # governor CPU
#   --bbr [on|off]  # activa o desactiva BBR + fq

set -euo pipefail

APPLY=0
PREEMPT_MODE=""
GOVERNOR="performance"
BBR="on"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    --preempt) PREEMPT_MODE="${2:-}"; shift 2 ;;
    --governor) GOVERNOR="${2:-performance}"; shift 2 ;;
    --bbr) BBR="${2:-on}"; shift 2 ;;
    -h|--help)
      sed -n '1,60p' "$0" | sed 's/^# //;t;d'
      exit 0
      ;;
    *) echo "[WARN] Opción desconocida: $1" >&2; shift ;;
  esac
done

info() { echo "[INFO] $*"; }
warn() { echo "[WARN] $*"; }
err()  { echo "[ERROR] $*"; }

have() { command -v "$1" >/dev/null 2>&1; }

show_preempt() {
  local runtime=""; local config=""; local f=""
  for f in /sys/kernel/debug/sched/preempt /sys/kernel/sched/preempt; do
    if [[ -r "$f" ]]; then
      runtime=$(tr -d '\n' < "$f" || true)
      break
    fi
  done
  if [[ -n "$runtime" ]]; then
    info "Modo de preempción (runtime): $runtime"
  else
    warn "No pude leer el modo de preempción en runtime (se requiere debugfs/sched)"
  fi
  local uname_rel
  uname_rel=$(uname -r)
  local cfg="/boot/config-${uname_rel}"
  if [[ -r "$cfg" ]]; then
    config=$(grep -E 'CONFIG_PREEMPT(_DYNAMIC)?=' "$cfg" | tr '\n' ' ' || true)
    info "Kernel config: ${config:-desconocido}"
  elif [[ -r /proc/config.gz ]] && have zcat; then
    config=$(zcat /proc/config.gz | grep -E 'CONFIG_PREEMPT(_DYNAMIC)?=' | tr '\n' ' ' || true)
    info "Kernel config: ${config:-desconocido}"
  else
    warn "No pude leer la configuración del kernel (config no disponible)"
  fi
}

apply_preempt() {
  [[ -z "${PREEMPT_MODE}" ]] && return 0
  local path=""
  if [[ ! -e /sys/kernel/debug ]]; then
    if [[ "$APPLY" -eq 1 ]]; then
      info "Montando debugfs en /sys/kernel/debug"
      sudo mount -t debugfs none /sys/kernel/debug || true
    fi
  fi
  if [[ -w /sys/kernel/debug/sched/preempt ]]; then
    path=/sys/kernel/debug/sched/preempt
  elif [[ -w /sys/kernel/sched/preempt ]]; then
    path=/sys/kernel/sched/preempt
  fi
  if [[ -n "$path" ]]; then
    if [[ "$APPLY" -eq 1 ]]; then
      info "Cambiando modo de preempción a: ${PREEMPT_MODE}"
      echo "$PREEMPT_MODE" | sudo tee "$path" >/dev/null || warn "No se pudo escribir en $path"
    else
      info "Sugerencia: echo ${PREEMPT_MODE} | sudo tee ${path}"
    fi
  else
    warn "No encontré punto de control para PREEMPT dinámico. Alternativa: agregar 'preempt=${PREEMPT_MODE}' al GRUB y reiniciar."
  fi
}

show_governor() {
  local gpath="/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
  if [[ -r "$gpath" ]]; then
    info "CPU governor (cpu0): $(cat "$gpath")"
  else
    warn "No se pudo leer governor desde cpufreq. Intentá cpupower."
  fi
}

apply_governor() {
  if [[ "$APPLY" -ne 1 ]]; then
    info "Sugerencia governor: performance → --governor ${GOVERNOR}"
    return 0
  fi
  if have cpupower; then
    info "Ajustando governor con cpupower: ${GOVERNOR}"
    sudo cpupower frequency-set -g "$GOVERNOR" || warn "cpupower falló"
  else
    warn "cpupower no encontrado, intento vía sysfs."
    for p in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
      [[ -w "$p" ]] || continue
      echo "$GOVERNOR" | sudo tee "$p" >/dev/null || true
    done
  fi
}

show_bbr() {
  if have sysctl; then
    info "TCP cc: $(sysctl -n net.ipv4.tcp_congestion_control 2>/dev/null || echo n/d)"
    info "qdisc:  $(sysctl -n net.core.default_qdisc 2>/dev/null || echo n/d)"
  else
    warn "sysctl no disponible para consultar BBR/qdisc"
  fi
}

apply_bbr() {
  if [[ "$APPLY" -ne 1 ]]; then
    info "Sugerencia BBR: ${BBR} (requiere sysctl)"
    return 0
  fi
  if [[ "$BBR" == "on" ]]; then
    info "Activando fq + bbr (runtime)"
    sudo sysctl -w net.core.default_qdisc=fq >/dev/null || true
    sudo sysctl -w net.ipv4.tcp_congestion_control=bbr >/dev/null || true
  else
    info "Restaurando cubic + fq_codel (aprox)"
    sudo sysctl -w net.core.default_qdisc=fq_codel >/dev/null || true
    sudo sysctl -w net.ipv4.tcp_congestion_control=cubic >/dev/null || true
  fi
}

main() {
  info "Chequeando estado actual"
  show_preempt
  show_governor
  show_bbr

  if [[ "$APPLY" -eq 1 ]]; then
    info "Aplicando cambios solicitados"
    apply_preempt
    apply_governor
    apply_bbr
    info "Listo. Verificá nuevamente arriba. Considerá persistir sysctl en /etc/sysctl.d/ si te sirve."
  else
    info "Modo sólo-lectura. Agregá --apply para ejecutar cambios (usará sudo)."
  fi
}

main "$@"

