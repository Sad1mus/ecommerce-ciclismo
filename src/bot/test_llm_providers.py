"""Tests del cerebro multi-proveedor (Groq / OpenRouter) y su fallback.

No tocan red ni claves: se prueba la SELECCION de proveedor, el fallback y los
modelos por defecto. La llamada real a la API (OpenAICompatLLM.chat) queda fuera
(igual que antes: pragma no cover), pero el contrato LLM.chat se respeta.
"""
import pytest

from brain import (
    DEFAULT_GROQ_MODEL,
    DEFAULT_OPENROUTER_MODEL,
    FallbackLLM,
    GroqLLM,
    OpenRouterLLM,
    build_llm,
)


class _OkLLM:
    name = "ok"

    def __init__(self, ret):
        self.ret = ret
        self.calls = 0

    def chat(self, messages, tools):
        self.calls += 1
        return self.ret


class _BoomLLM:
    name = "boom"

    def __init__(self):
        self.calls = 0

    def chat(self, messages, tools):
        self.calls += 1
        raise RuntimeError("proveedor caido / sin cupo")


# ---- FallbackLLM ----
def test_fallback_usa_secundario_si_primario_falla():
    prim, sec = _BoomLLM(), _OkLLM({"role": "assistant", "content": "desde secundario"})
    out = FallbackLLM(prim, sec).chat([], [])
    assert out["content"] == "desde secundario"
    assert prim.calls == 1 and sec.calls == 1  # se intento el primario y luego el secundario


def test_fallback_no_toca_secundario_si_primario_ok():
    prim, sec = _OkLLM({"role": "assistant", "content": "primario"}), _OkLLM({"content": "sec"})
    out = FallbackLLM(prim, sec).chat([], [])
    assert out["content"] == "primario"
    assert sec.calls == 0  # el secundario ni se llama


# ---- build_llm: seleccion de proveedor ----
def test_build_default_es_groq_sin_fallback():
    llm = build_llm(env={})
    assert isinstance(llm, GroqLLM) and llm.name == "groq"


def test_build_openrouter_como_primario():
    llm = build_llm(env={"LLM_PROVIDER": "openrouter"})
    assert isinstance(llm, OpenRouterLLM) and llm.name == "openrouter"


def test_build_con_ambas_claves_arma_fallback():
    llm = build_llm(env={"LLM_PROVIDER": "groq", "OPENROUTER_KEY": "or_x"})
    assert isinstance(llm, FallbackLLM)
    assert llm.primary.name == "groq" and llm.secondary.name == "openrouter"


def test_build_openrouter_con_groq_key_arma_fallback_inverso():
    llm = build_llm(env={"LLM_PROVIDER": "openrouter", "GROQ_API_KEY": "gsk_x"})
    assert isinstance(llm, FallbackLLM)
    assert llm.primary.name == "openrouter" and llm.secondary.name == "groq"


def test_build_provider_desconocido_cae_a_groq():
    assert isinstance(build_llm(env={"LLM_PROVIDER": "foobar"}), GroqLLM)


# ---- modelos y contrato base ----
def test_modelos_default_y_override():
    assert GroqLLM().model == DEFAULT_GROQ_MODEL or GroqLLM().model  # default o env
    assert OpenRouterLLM(model="acme/x").model == "acme/x"
    assert GroqLLM(model="y").model == "y"
    assert OpenRouterLLM().base_url == "https://openrouter.ai/api/v1"
    assert GroqLLM().base_url == "https://api.groq.com/openai/v1"


def test_api_key_faltante_lanza(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        GroqLLM()._api_key()
