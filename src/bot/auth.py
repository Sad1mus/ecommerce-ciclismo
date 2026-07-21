"""Control de acceso del bot por chat_id (allowlist).

El bot OPERA el negocio (crea/confirma/factura/despacha pedidos), asi que en
produccion NO debe responder a cualquiera que lo encuentre en Telegram. La
allowlist se arma con los chat_id autorizados del dueño y la bodega, tomados de
las variables de entorno ya previstas en `.env` (`ADMIN_CHAT_ID`, `BODEGA_CHAT_ID`)
y, opcionalmente, `TELEGRAM_ALLOWED_CHAT_IDS` (lista separada por comas).

Comportamiento (a proposito, para no dejar afuera al dueño no vidente por una
config faltante):
 - allowlist VACIA (ninguna variable configurada) -> el bot queda ABIERTO, como
   en la demo/dev, y al arrancar se registra un WARNING bien visible.
 - allowlist con al menos un chat_id -> se APLICA estrictamente: solo esos chat_id
   operan; a cualquier otro se le responde con una negativa cortes y el intento
   queda logueado (rastro de acceso).

Este modulo es logica pura y testeable: no importa python-telegram-bot ni toca red.
"""
from __future__ import annotations

import logging
import os
from typing import Iterable, Mapping

logger = logging.getLogger("bot.auth")

# Variables de entorno de las que se arma la allowlist. Cada una admite varios
# chat_id separados por comas (util si la bodega tiene mas de un operario).
ALLOWLIST_ENV_VARS = ("ADMIN_CHAT_ID", "BODEGA_CHAT_ID", "TELEGRAM_ALLOWED_CHAT_IDS")

DENEGADO = "Lo siento, no tienes permiso para usar este asistente."


def load_allowlist(env: Mapping[str, str] | None = None) -> set[str]:
    """Lee los chat_id autorizados del entorno. Devuelve un set de strings.

    No inventa ni asume: solo recoge lo que este configurado (vacios se ignoran).
    """
    env = env if env is not None else os.environ
    ids: set[str] = set()
    for var in ALLOWLIST_ENV_VARS:
        raw = env.get(var, "") or ""
        for piece in raw.split(","):
            piece = piece.strip()
            if piece:
                ids.add(piece)
    return ids


def is_allowed(chat_id: str | int, allowlist: Iterable[str]) -> bool:
    """True si el chat_id puede operar el bot.

    Regla deliberada: si la allowlist esta vacia, el bot esta ABIERTO (dev/demo) y
    todo chat_id pasa. Con la allowlist configurada, solo pasan los de la lista.
    """
    allow = set(allowlist)
    if not allow:
        return True  # sin allowlist: bot abierto (se avisa por WARNING al arrancar)
    return str(chat_id) in allow


def describe(allowlist: Iterable[str]) -> str:
    """Frase de estado para loguear al arrancar (dueño ve si el bot esta protegido)."""
    allow = set(allowlist)
    if not allow:
        return (
            "SEGURIDAD: bot ABIERTO. No hay allowlist (ADMIN_CHAT_ID/BODEGA_CHAT_ID "
            "vacios): CUALQUIERA que encuentre el bot puede operar el negocio. "
            "Configura los chat_id autorizados antes de exponerlo."
        )
    return f"SEGURIDAD: bot RESTRINGIDO a {len(allow)} chat_id autorizados."


def log_startup_state(allowlist: Iterable[str]) -> None:
    """Registra el estado de acceso al arrancar: WARNING si esta abierto, INFO si no."""
    allow = set(allowlist)
    if not allow:
        logger.warning(describe(allow))
    else:
        logger.info(describe(allow))
