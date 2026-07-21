"""Tests unitarios de MedusaClient con una Session HTTP simulada (sin red).

Foco: el fix del bug de escala en get_order. Antes miraba solo los 50 pedidos
mas recientes y filtraba en memoria -> un pedido viejo devolvia None en silencio.
Ahora pagina hasta encontrarlo (o agotar), asi que lo halla aunque haya cientos.
"""
from __future__ import annotations

from medusa_client import MedusaClient


class _FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class _PagedOrdersSession:
    """Session falsa: /admin/orders devuelve pedidos paginados por offset/limit.

    Cuenta las llamadas para verificar que efectivamente se pagino (>1 pagina).
    """

    def __init__(self, orders):
        self._orders = orders          # lista completa, ya ordenada (nuevos primero)
        self.requests = 0

    def request(self, method, url, headers=None, params=None, timeout=None, **kw):
        self.requests += 1
        offset = int((params or {}).get("offset", 0))
        limit = int((params or {}).get("limit", 100))
        chunk = self._orders[offset:offset + limit]
        return _FakeResp({"orders": chunk})


def _order(display_id):
    return {
        "id": f"order_{display_id}",
        "display_id": display_id,
        "status": "pending",
        "payment_status": "captured",
        "fulfillment_status": "not_fulfilled",
        "total": 1000,
        "currency_code": "cop",
        "metadata": {},
        "items": [{"title": "Candado", "quantity": 1}],
    }


def _client(session):
    # admin_token fijo -> evita el login (no toca /auth).
    return MedusaClient(base_url="http://x", admin_token="tok", session=session)


def test_get_order_encuentra_pedido_viejo_mas_alla_de_los_50():
    # 250 pedidos, del mas nuevo (250) al mas viejo (1). El pedido 5 es "viejo":
    # con el codigo anterior (solo 50 recientes) habria dado None.
    orders = [_order(i) for i in range(250, 0, -1)]
    session = _PagedOrdersSession(orders)
    det = _client(session).get_order(5, page=100)
    assert det is not None
    assert det.display_id == 5
    assert det.items and det.items[0].title == "Candado"
    assert session.requests >= 3  # necesito paginar (5 esta en la 3a pagina)


def test_get_order_devuelve_none_si_no_existe_sin_inventar():
    orders = [_order(i) for i in range(120, 0, -1)]
    session = _PagedOrdersSession(orders)
    det = _client(session).get_order(9999, page=100)
    assert det is None  # anti-alucinacion: no existe -> None, nunca un pedido inventado


def test_get_order_para_de_paginar_al_agotar_los_pedidos():
    # Solo 10 pedidos: no debe seguir pidiendo paginas vacias indefinidamente.
    orders = [_order(i) for i in range(10, 0, -1)]
    session = _PagedOrdersSession(orders)
    det = _client(session).get_order(9999, page=100)
    assert det is None
    assert session.requests == 1  # una sola pagina (vino incompleta -> corta)
