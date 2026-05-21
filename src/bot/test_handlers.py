"""Tests de los handlers del bot con Medusa MOCKEADO (sin red ni token real).

Cubren las tres garantias exigidas por la Fase 2:
  (a) /stock devuelve EXACTAMENTE el stock que entrega la API.
  (b) ante un fallo de la API el bot NO inventa: responde "dato no disponible".
  (c) la salida es apta para lector de pantalla: sin emojis ni tablas.
"""
import handlers
from formatting import DATO_NO_DISPONIBLE, has_emoji, is_screen_reader_safe
from medusa_client import OrderInfo, ProductInfo


class FakeClient:
    """Cliente Medusa simulado que devuelve datos controlados."""

    def __init__(self, productos=None, pedidos=None):
        self._productos = productos or []
        self._pedidos = pedidos or []

    def search_products(self, query, limit=5):
        return self._productos

    def list_orders(self, limit=5):
        return self._pedidos


class FailingClient:
    """Cliente que simula la API caida: toda llamada lanza excepcion."""

    def search_products(self, query, limit=5):
        raise RuntimeError("API caida")

    def list_orders(self, limit=5):
        raise ConnectionError("API caida")


# ---------- (a) /stock refleja el stock de la API ----------
def test_stock_devuelve_el_valor_de_la_api():
    cliente = FakeClient(
        productos=[ProductInfo(title="Candado espiral", sku="CL1", price=14500, currency="COP", stock=8)]
    )
    salida = handlers.handle_stock(cliente, "candado")
    assert "8 unidades" in salida
    assert "Candado espiral" in salida


def test_stock_no_inventa_si_la_api_no_da_cantidad():
    cliente = FakeClient(
        productos=[ProductInfo(title="Bomba mini", sku="B1", price=18500, currency="COP", stock=None)]
    )
    salida = handlers.handle_stock(cliente, "bomba")
    assert "stock no disponible" in salida


def test_precio_devuelve_el_valor_de_la_api():
    cliente = FakeClient(
        productos=[ProductInfo(title="Forro gel MTB", sku="F1", price=19500, currency="COP", stock=43)]
    )
    salida = handlers.handle_precio(cliente, "forro")
    assert "19.500" in salida
    assert "Forro gel MTB" in salida


def test_pedidos_devuelve_lo_de_la_api():
    cliente = FakeClient(
        pedidos=[OrderInfo(display_id=1001, status="completed", total=34000, currency="COP")]
    )
    salida = handlers.handle_pedidos(cliente)
    assert "1001" in salida
    assert "completed" in salida
    assert "34.000" in salida


# ---------- (b) ante fallo de la API, no inventa ----------
def test_stock_api_caida_responde_dato_no_disponible():
    salida = handlers.handle_stock(FailingClient(), "candado")
    assert salida == DATO_NO_DISPONIBLE
    # No debe aparecer ningun digito (no inventa cifras).
    assert not any(c.isdigit() for c in salida)


def test_precio_api_caida_no_inventa():
    salida = handlers.handle_precio(FailingClient(), "candado")
    assert salida == DATO_NO_DISPONIBLE
    assert "$" not in salida


def test_pedidos_api_caida_no_inventa():
    salida = handlers.handle_pedidos(FailingClient())
    assert salida == DATO_NO_DISPONIBLE


# ---------- (c) salida apta para lector de pantalla ----------
def test_salida_sin_emojis_ni_tablas():
    cliente = FakeClient(
        productos=[
            ProductInfo(title="Candado espiral", sku="CL1", price=14500, currency="COP", stock=8),
            ProductInfo(title="Bomba mini", sku="B1", price=18500, currency="COP", stock=3),
        ]
    )
    for salida in (
        handlers.handle_stock(cliente, "x"),
        handlers.handle_precio(cliente, "x"),
        handlers.handle_pedidos(FakeClient(pedidos=[OrderInfo(1, "pending", 1000, "COP")])),
        DATO_NO_DISPONIBLE,
    ):
        assert not has_emoji(salida)
        assert "|" not in salida and "\t" not in salida
        assert is_screen_reader_safe(salida)


def test_clamp_no_supera_10_lineas():
    muchos = [
        ProductInfo(title=f"Producto {i}", sku=str(i), price=1000, currency="COP", stock=i)
        for i in range(30)
    ]
    salida = handlers.handle_stock(FakeClient(productos=muchos), "x")
    assert len(salida.splitlines()) <= 10
