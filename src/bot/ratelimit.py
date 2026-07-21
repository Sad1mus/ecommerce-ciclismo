"""Rate-limit por chat_id para el bot.

El cerebro llama a un LLM con cupo diario (Groq free = 100k tokens/dia). Sin limite,
el spam de un chat quema el cupo y calla el negocio (y, sin allowlist, un ajeno
podria hacerlo a proposito). Este limitador acota los mensajes por chat en una
ventana DESLIZANTE.

El reloj es inyectable (`clock`) para poder testear sin depender del tiempo real.
"""
from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from typing import Callable, Deque, Dict

DEFAULT_MAX_CALLS = 20      # mensajes por ventana y por chat (generoso para un humano)
DEFAULT_WINDOW_SECONDS = 60


class RateLimiter:
    """Ventana deslizante por chat_id: hasta `max_calls` mensajes cada `window` segundos."""

    def __init__(
        self,
        max_calls: int = DEFAULT_MAX_CALLS,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_calls = max(1, int(max_calls))
        self.window = max(1, int(window_seconds))
        self._clock = clock
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, chat_id: str) -> bool:
        """True si el chat puede enviar ahora; registra el hit. False si supero el cupo."""
        now = self._clock()
        hits = self._hits[str(chat_id)]
        limite = now - self.window
        while hits and hits[0] <= limite:
            hits.popleft()
        if len(hits) >= self.max_calls:
            return False
        hits.append(now)
        return True


def build_rate_limiter(env: dict | None = None) -> RateLimiter:
    """Construye el limitador desde el entorno (RATE_LIMIT_MAX / RATE_LIMIT_WINDOW)."""
    env = env if env is not None else os.environ

    def _int(name: str, default: int) -> int:
        try:
            return int(env.get(name, "") or default)
        except (TypeError, ValueError):
            return default

    return RateLimiter(
        _int("RATE_LIMIT_MAX", DEFAULT_MAX_CALLS),
        _int("RATE_LIMIT_WINDOW", DEFAULT_WINDOW_SECONDS),
    )
