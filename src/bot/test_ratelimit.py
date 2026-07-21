"""Tests del rate-limit por chat_id (ventana deslizante, reloj inyectado)."""
from ratelimit import RateLimiter, build_rate_limiter


class FakeClock:
    """Reloj controlable: avanza solo cuando se lo pide el test."""

    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


def test_permite_hasta_el_cupo_y_luego_corta():
    clk = FakeClock()
    rl = RateLimiter(max_calls=3, window_seconds=60, clock=clk)
    assert [rl.allow("c") for _ in range(3)] == [True, True, True]
    assert rl.allow("c") is False  # 4to en la misma ventana: cortado


def test_la_ventana_se_reinicia_al_pasar_el_tiempo():
    clk = FakeClock()
    rl = RateLimiter(max_calls=2, window_seconds=60, clock=clk)
    assert rl.allow("c") and rl.allow("c")
    assert rl.allow("c") is False
    clk.advance(61)               # pasa la ventana
    assert rl.allow("c") is True  # vuelve a permitir


def test_el_limite_es_por_chat():
    clk = FakeClock()
    rl = RateLimiter(max_calls=1, window_seconds=60, clock=clk)
    assert rl.allow("dueño") is True
    assert rl.allow("dueño") is False
    assert rl.allow("bodega") is True   # otro chat no se ve afectado


def test_build_lee_env_y_tiene_defaults():
    rl = build_rate_limiter(env={"RATE_LIMIT_MAX": "5", "RATE_LIMIT_WINDOW": "30"})
    assert rl.max_calls == 5 and rl.window == 30
    rl2 = build_rate_limiter(env={})           # sin config: defaults sanos
    assert rl2.max_calls >= 1 and rl2.window >= 1
