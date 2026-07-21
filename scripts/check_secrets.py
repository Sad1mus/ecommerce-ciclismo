#!/usr/bin/env python3
"""Guarda de secretos de produccion: aborta el deploy si hay placeholders o vacios.

La usa scripts/deploy.sh ANTES de arrancar el stack: si JWT_SECRET o COOKIE_SECRET
siguen con el valor de ejemplo 'cambia-esto-en-produccion' (o estan vacios), el
deploy falla. Asi produccion nunca arranca con los secretos por defecto del repo.

Solo stdlib: corre en el VPS sin dependencias. La logica (`validate`) esta cubierta
por tests (src/bot/test_check_secrets.py).
"""
from __future__ import annotations

import sys

PLACEHOLDER = "cambia-esto-en-produccion"
# Secretos que DEBEN estar presentes y NO pueden quedar con el valor de ejemplo.
CRITICOS = ("JWT_SECRET", "COOKIE_SECRET")


def load_env_file(path: str) -> dict | None:
    """Lee KEY=VALUE de un .env a un dict. Devuelve None si el archivo no existe."""
    env: dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    except FileNotFoundError:
        return None
    return env


def validate(env: dict) -> list[str]:
    """Devuelve la lista de problemas (vacia = todo bien)."""
    problemas: list[str] = []
    for name in CRITICOS:
        val = (env.get(name) or "").strip()
        if not val:
            problemas.append(f"{name} esta vacio")
        elif val == PLACEHOLDER:
            problemas.append(f"{name} sigue con el valor de ejemplo '{PLACEHOLDER}'")
    return problemas


def main(argv: list[str]) -> int:
    path = argv[1] if len(argv) > 1 else ".env"
    env = load_env_file(path)
    if env is None:
        print(f"ERROR: no existe {path} (secretos de produccion).", file=sys.stderr)
        return 1
    problemas = validate(env)
    if problemas:
        print("ERROR: secretos de produccion invalidos:", file=sys.stderr)
        for p in problemas:
            print(f"  - {p}", file=sys.stderr)
        print("Corrige .env antes del deploy (ver docs/deploy-vps.md).", file=sys.stderr)
        return 1
    print("Secretos de produccion OK (sin placeholders ni vacios criticos).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
