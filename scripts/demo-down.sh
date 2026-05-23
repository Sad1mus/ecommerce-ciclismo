#!/usr/bin/env bash
# ===========================================================================
# demo-down.sh — Apaga limpiamente la demo local que levanta dev-up.sh:
# bot, storefront, Medusa, el inhibidor de suspension (keep-awake) y, por
# ultimo, Postgres+Redis. Idempotente: no falla si algo ya estaba apagado.
# ===========================================================================
set -uo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
LOGDIR="$ROOT/.devlogs"

stop_pid() { # archivo_pid nombre
  local f="$1" name="$2"
  if [ -f "$f" ] && kill -0 "$(cat "$f")" 2>/dev/null; then
    kill "$(cat "$f")" 2>/dev/null && echo "  $name detenido (pid $(cat "$f"))"
  else
    echo "  $name no estaba corriendo"
  fi
  rm -f "$f"
}

echo ">> Apagando procesos de la demo"
stop_pid "$LOGDIR/bot.pid" "bot"
stop_pid "$LOGDIR/storefront.pid" "storefront"
stop_pid "$LOGDIR/medusa.pid" "medusa"
# Respaldo: por si quedaron hijos sin pid file.
pkill -f "next start -p 8000" 2>/dev/null || true
pkill -f "medusa develop"     2>/dev/null || true
pkill -f "src/bot/bot.py"     2>/dev/null || true

echo ">> Liberando keep-awake (systemd-inhibit)"
stop_pid "$LOGDIR/keepawake.pid" "keep-awake"
pkill -f "systemd-inhibit.*ciclismo-demo" 2>/dev/null || true

echo ">> Deteniendo Postgres + Redis (datos se conservan)"
docker compose stop postgres redis >/dev/null 2>&1 && echo "  contenedores detenidos" || echo "  docker ya estaba parado"

echo "Demo apagada."
