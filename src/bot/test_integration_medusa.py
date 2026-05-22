"""Tests de INTEGRACION contra el Medusa REAL (sin mocks).

Verifican la regla ANTI-ALUCINACION de punta a punta: el stock y el precio que
reporta el bot coinciden EXACTAMENTE con lo que entrega la Store API de Medusa
(fuente unica de verdad). Requieren el stack vivo en :9001.

Marcados @pytest.mark.integration -> EXCLUIDOS por defecto (`pytest`). Correr con:
    python -m pytest -q -m integration
"""
from __future__ import annotations

import handlers
from conftest import store_products
from medusa_client import MedusaClient

import pytest

pytestmark = pytest.mark.integration


def _ref_skus(cfg, minimo):
    """Toma productos REALES de la Store API y devuelve hasta `minimo*2` candidatos
    (titulo, sku, inventory_quantity, precio) con stock entero, para comparar.
    """
    ref = []
    for p in store_products(cfg, limit=30):
        variants = p.get("variants") or []
        if not variants:
            continue
        v = variants[0]
        inv = v.get("inventory_quantity")
        sku = v.get("sku")
        if isinstance(inv, int) and sku:
            cp = v.get("calculated_price") or {}
            ref.append((p.get("title", ""), sku, inv, cp.get("calculated_amount")))
        if len(ref) >= minimo * 2:
            break
    return ref


def test_bot_stock_coincide_con_store_api(medusa_cfg):
    """El stock que reporta el bot == inventory_quantity de la API, para >=3 SKUs."""
    candidatos = _ref_skus(medusa_cfg, minimo=3)
    assert len(candidatos) >= 3, "Se necesitan >=3 SKUs reales con stock en la API"

    client = MedusaClient()  # cliente REAL: lee MEDUSA_* del entorno, golpea :9001
    comparados = 0
    print("\n  SKU            | API inv | bot stock | precio API | OK")
    print("  ---------------+---------+-----------+------------+----")
    for title, sku, inv, price in candidatos:
        infos = client.search_products(title)
        match = next((i for i in infos if i.sku == sku), None)
        if match is None:
            continue  # la busqueda por texto no devolvio este SKU; probamos otro
        assert match.stock == inv, f"{sku}: bot={match.stock} != API={inv}"
        # El comando /stock debe reflejar el dato real en su salida al usuario.
        salida = handlers.handle_stock(client, title)
        assert f"{title}: {inv} unidades" in salida, f"/stock no refleja {sku}"
        print(f"  {sku:<14} | {inv:>7} | {match.stock:>9} | {str(price):>10} | si")
        comparados += 1
        if comparados >= 3:
            break

    assert comparados >= 3, f"Solo se pudieron comparar {comparados} SKUs (se piden >=3)"
    print(f"\n  -> {comparados} SKUs reales: el stock del bot coincide con la Store API.")
