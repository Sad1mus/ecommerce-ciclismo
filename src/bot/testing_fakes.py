"""Dobles de prueba compartidos (no es un modulo de tests; pytest no lo recoge).

Permiten testear toda la logica con Medusa y el LLM MOCKEADOS: sin red, sin
tokens, sin GROQ_API_KEY ni OPENAI_API_KEY.
"""
from __future__ import annotations

import json


class FakeClient:
    """Cliente Medusa simulado con datos controlados."""

    def __init__(self, productos=None, pedidos=None, detalles=None, categorias=None, por_codigo=None):
        self._productos = productos or []
        self._pedidos = pedidos or []
        # detalles: dict display_id -> OrderDetail (para get_order).
        self._detalles = detalles or {}
        self._categorias = categorias or []  # [{name, is_active}]
        self._por_codigo = por_codigo or {}  # {codigo: [titulos]}
        self.escrituras = []  # registro de mutaciones para asserts

    def search_products(self, query, limit=5):
        return self._productos[:limit]

    def list_orders(self, limit=5):
        return self._pedidos[:limit]

    def get_order(self, display_id, search_limit=50):
        return self._detalles.get(int(display_id))

    def create_order(self, items, email=None):
        self.escrituras.append(("create_order", items, email))
        from medusa_client import OrderDetail
        return OrderDetail(
            id="order_nuevo", display_id=999, status="pending", payment_status="",
            fulfillment_status="", total=0, currency="COP", items=[], metadata={},
        )

    def update_order_metadata(self, order_id, nuevos, actuales=None):
        self.escrituras.append(("update_metadata", order_id, nuevos))
        fusion = dict(actuales or {})
        fusion.update(nuevos)
        return fusion

    def list_categories(self):
        return [{"id": f"pcat_{i}", "name": c["name"], "is_active": c["is_active"]}
                for i, c in enumerate(self._categorias)]

    def products_in_category(self, name, limit=20):
        match = next((c for c in self._categorias if c["is_active"] and c["name"].lower() == name.lower()), None)
        if match is None:
            return None
        return self._productos[:limit]

    def products_by_codigo(self, codigo, max_total=800):
        return list(self._por_codigo.get(codigo.strip().upper(), []))


class FailingClient:
    """Simula la API caida: toda llamada lanza excepcion."""

    def search_products(self, query, limit=5):
        raise RuntimeError("API caida")

    def list_orders(self, limit=5):
        raise ConnectionError("API caida")

    def get_order(self, display_id, search_limit=50):
        raise RuntimeError("API caida")


# ---- LLM falso (cerebro conversacional sin red) ----
def msg_texto(content):
    """Mensaje 'assistant' de texto plano (respuesta final)."""
    return {"role": "assistant", "content": content}


def msg_tool_call(name, args, call_id="c1"):
    """Mensaje 'assistant' que pide ejecutar una herramienta."""
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(args)},
            }
        ],
    }


class FakeLLM:
    """LLM programado: devuelve respuestas en orden en cada llamada a chat()."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []  # historial de 'messages' visto en cada llamada

    def chat(self, messages, tools):
        self.calls.append(list(messages))
        if not self._responses:
            return {"role": "assistant", "content": "(sin mas respuestas programadas)"}
        return self._responses.pop(0)


class FailingLLM:
    """LLM caido: chat() siempre lanza (para probar la degradacion segura)."""

    def chat(self, messages, tools):
        raise RuntimeError("LLM no disponible")


class FakeTranscriber:
    """STT falso: devuelve un texto fijo en vez de transcribir audio real."""

    def __init__(self, texto: str):
        self.texto = texto

    def transcribe(self, audio: bytes) -> str:
        return self.texto


class FailingTranscriber:
    """STT que falla (audio corrupto, sin clave, etc.)."""

    def transcribe(self, audio: bytes) -> str:
        raise RuntimeError("no se pudo transcribir")
