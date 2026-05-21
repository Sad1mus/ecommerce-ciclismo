"""Dobles de prueba compartidos (no es un modulo de tests; pytest no lo recoge).

Permiten testear toda la logica con Medusa MOCKEADO: sin red, sin tokens,
sin OPENAI_API_KEY.
"""
from __future__ import annotations


class FakeClient:
    """Cliente Medusa simulado con datos controlados."""

    def __init__(self, productos=None, pedidos=None):
        self._productos = productos or []
        self._pedidos = pedidos or []

    def search_products(self, query, limit=5):
        return self._productos[:limit]

    def list_orders(self, limit=5):
        return self._pedidos[:limit]


class FailingClient:
    """Simula la API caida: toda llamada lanza excepcion."""

    def search_products(self, query, limit=5):
        raise RuntimeError("API caida")

    def list_orders(self, limit=5):
        raise ConnectionError("API caida")


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
