"""Tests del historial: memoria, Redis (con doble) y degradacion segura."""
import history
from history import MemoryHistoryStore, RedisHistoryStore, build_history_store


class FakeRedis:
    """Doble minimo de Redis: dict con get/set(ex)/delete."""

    def __init__(self):
        self.store = {}

    def get(self, k):
        return self.store.get(k)

    def set(self, k, v, ex=None):
        self.store[k] = v

    def delete(self, k):
        self.store.pop(k, None)


class FailingRedis:
    """Redis caido: toda operacion lanza (para probar la degradacion a memoria)."""

    def get(self, k):
        raise RuntimeError("redis down")

    def set(self, k, v, ex=None):
        raise RuntimeError("redis down")

    def delete(self, k):
        raise RuntimeError("redis down")


MSGS = [{"role": "system", "content": "s"}, {"role": "user", "content": "hola"}]


def test_memory_store_roundtrip():
    s = MemoryHistoryStore()
    assert s.load("c") is None
    s.save("c", MSGS)
    assert s.load("c") == MSGS
    s.delete("c")
    assert s.load("c") is None


def test_redis_store_persiste_y_dos_instancias_comparten():
    r = FakeRedis()
    a = RedisHistoryStore(r)
    a.save("c", MSGS)
    # Otra instancia (simula otro proceso tras un reinicio) ve el mismo historial.
    b = RedisHistoryStore(r)
    assert b.load("c") == MSGS
    b.delete("c")
    assert a.load("c") is None


def test_redis_caido_degrada_a_memoria_sin_romper():
    s = RedisHistoryStore(FailingRedis())
    # No crashea: guarda en el respaldo en memoria y lo recupera de ahi.
    s.save("c", MSGS)
    assert s.load("c") == MSGS


def test_build_sin_redis_url_devuelve_memoria():
    store = build_history_store(url="")
    assert isinstance(store, MemoryHistoryStore)


def test_build_con_url_pero_sin_redis_degrada_a_memoria():
    # Si REDIS_URL esta pero la libreria/servidor no responde, cae a memoria (no crashea).
    store = build_history_store(url="redis://noexiste.invalid:6390")
    assert isinstance(store, MemoryHistoryStore)
