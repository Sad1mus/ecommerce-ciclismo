"""Almacenamiento del historial de conversacion del bot, por chat_id.

El cerebro (brain.py) guarda, por chat, la lista de mensajes de la conversacion.
En memoria se pierde con cada reinicio; con `restart=always` en produccion eso
corta cualquier conversacion en curso. Este modulo permite persistir en Redis (ya
esta en el stack) y DEGRADAR a memoria si Redis no esta disponible (dev/test o
Redis caido), sin crashear ni inventar.

El import de `redis` es DIFERIDO: los tests no necesitan la libreria ni un Redis vivo.
"""
from __future__ import annotations

import json
import logging
import os
from typing import List, Protocol

logger = logging.getLogger("bot.history")

HISTORY_TTL_SECONDS = 60 * 60 * 24  # 24h: una conversacion vieja no revive para siempre
KEY_PREFIX = "bot:hist:"


class HistoryStore(Protocol):
    def load(self, chat_id: str) -> List[dict] | None:  # pragma: no cover
        ...

    def save(self, chat_id: str, messages: List[dict]) -> None:  # pragma: no cover
        ...

    def delete(self, chat_id: str) -> None:  # pragma: no cover
        ...


class MemoryHistoryStore:
    """Historial en memoria del proceso (comportamiento historico: se pierde al reiniciar)."""

    def __init__(self) -> None:
        self._data: dict[str, List[dict]] = {}

    def load(self, chat_id: str) -> List[dict] | None:
        return self._data.get(chat_id)

    def save(self, chat_id: str, messages: List[dict]) -> None:
        self._data[chat_id] = messages

    def delete(self, chat_id: str) -> None:
        self._data.pop(chat_id, None)


class RedisHistoryStore:
    """Historial en Redis (sobrevive reinicios). Serializa la lista de mensajes a JSON.

    Ante CUALQUIER fallo de Redis degrada a un respaldo en memoria: no crashea y no
    inventa (si no puede leer, se arranca una conversacion nueva).
    """

    def __init__(self, redis_client, ttl: int = HISTORY_TTL_SECONDS) -> None:
        self._r = redis_client
        self._ttl = ttl
        self._fallback = MemoryHistoryStore()

    def _key(self, chat_id: str) -> str:
        return f"{KEY_PREFIX}{chat_id}"

    def load(self, chat_id: str) -> List[dict] | None:
        try:
            raw = self._r.get(self._key(chat_id))
        except Exception as e:  # noqa: BLE001 - Redis caido: degradar, no romper
            logger.warning("Redis load fallo (%s); uso memoria", type(e).__name__)
            return self._fallback.load(chat_id)
        if raw is None:
            return None
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None  # dato corrupto: mejor conversacion nueva que reventar
        return data if isinstance(data, list) else None

    def save(self, chat_id: str, messages: List[dict]) -> None:
        try:
            self._r.set(self._key(chat_id), json.dumps(messages), ex=self._ttl)
        except Exception as e:  # noqa: BLE001
            logger.warning("Redis save fallo (%s); uso memoria", type(e).__name__)
            self._fallback.save(chat_id, messages)

    def delete(self, chat_id: str) -> None:
        try:
            self._r.delete(self._key(chat_id))
        except Exception as e:  # noqa: BLE001
            logger.warning("Redis delete fallo (%s)", type(e).__name__)
            self._fallback.delete(chat_id)


def build_history_store(url: str | None = None) -> HistoryStore:
    """Elige el store segun el entorno: Redis si hay REDIS_URL y la libreria; si no, memoria.

    No falla si Redis no esta: degrada a memoria con un aviso (util en dev/test).
    """
    url = url if url is not None else os.getenv("REDIS_URL", "")
    if not url:
        logger.info("Sin REDIS_URL: historial en memoria (se pierde al reiniciar).")
        return MemoryHistoryStore()
    try:
        import redis  # import diferido: no requerido para los tests
        client = redis.Redis.from_url(url, decode_responses=True)
        client.ping()
    except Exception as e:  # noqa: BLE001 - sin Redis vivo: seguir en memoria
        logger.warning("Redis no disponible (%s): historial en memoria.", type(e).__name__)
        return MemoryHistoryStore()
    logger.info("Historial en Redis (%s).", url)
    return RedisHistoryStore(client)
