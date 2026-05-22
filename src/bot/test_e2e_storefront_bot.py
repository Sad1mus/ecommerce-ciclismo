"""E2E REAL (sin mocks): una sola fuente de verdad para storefront y bot.

Para un SKU real comprueba que el STOCK coincide entre tres fuentes
independientes —Admin API (stocked_quantity en la bodega), bot (MedusaClient) y
Store API (inventory_quantity)— y que el PRECIO que renderiza el storefront es el
mismo que reporta el bot. Requiere el stack vivo (scripts/dev-up.sh).

    python -m pytest -q -m integration
"""
from __future__ import annotations

import os

import pytest
import requests

import handlers
from conftest import admin_stocked_quantity, store_products
from medusa_client import MedusaClient

pytestmark = pytest.mark.integration


def _pick_sku(cfg):
    """Primer producto real con SKU, handle, stock entero y precio."""
    for p in store_products(cfg, limit=20):
        v = (p.get("variants") or [{}])[0]
        inv = v.get("inventory_quantity")
        sku = v.get("sku")
        cp = v.get("calculated_price") or {}
        price = cp.get("calculated_amount")
        if sku and p.get("handle") and isinstance(inv, int) and isinstance(price, (int, float)):
            return {
                "title": p["title"],
                "handle": p["handle"],
                "sku": sku,
                "inv": inv,
                "price": int(price),
            }
    pytest.skip("No hay producto real con SKU+handle+stock+precio")


def test_e2e_storefront_bot_admin_misma_fuente(medusa_cfg, admin_token):
    prod = _pick_sku(medusa_cfg)
    title, sku, inv, price = prod["title"], prod["sku"], prod["inv"], prod["price"]

    # 1) ADMIN API — stocked_quantity real en la bodega (fuente de verdad DB).
    admin_stock = admin_stocked_quantity(medusa_cfg, admin_token, title).get(sku)
    assert admin_stock is not None, f"Admin API no devolvió stock para {sku}"

    # 2) BOT — cliente real contra :9001 (no mock).
    client = MedusaClient()
    infos = client.search_products(title)
    bot = next((i for i in infos if i.sku == sku), None)
    assert bot is not None, f"El bot no encontró el SKU {sku}"

    # 3) STOREFRONT — la página real del producto que ve el cliente.
    sf_base = os.environ.get("STOREFRONT_URL", "http://localhost:8000").rstrip("/")
    sess = requests.Session()
    page = sess.get(f"{sf_base}/co/products/{prod['handle']}", timeout=30)
    assert page.status_code == 200, f"Storefront devolvió {page.status_code}"
    html = page.text
    # El starter renderiza el precio con data-value="<monto>"; ese es el dato crudo.
    sf_price_ok = f'data-value="{price}"' in html
    assert sf_price_ok, f"El storefront no renderiza el precio {price} del SKU {sku}"
    assert title.split()[0] in html, "El storefront no muestra el producto esperado"

    # ---- Comparación visible: los valores coinciden entre fuentes ----
    print(f"\n  Producto real: '{title}'  (SKU {sku}, handle {prod['handle']})")
    print("  STOCK (unidades):")
    print(f"    Admin API (stocked_quantity) : {admin_stock}")
    print(f"    Bot (MedusaClient)           : {bot.stock}")
    print(f"    Store API (inventory_qty)    : {inv}")
    print("  PRECIO (COP, monto crudo):")
    print(f"    Bot (MedusaClient)           : {bot.price}")
    print(f"    Store API (calculated)       : {price}")
    print(f"    Storefront (data-value)      : {price}  (presente en la página: {sf_price_ok})")
    print(f"  /stock del bot -> {handlers.handle_stock(client, title).splitlines()[1]}")

    # Las tres fuentes de STOCK son iguales.
    assert admin_stock == bot.stock == inv, (
        f"Stock no coincide: admin={admin_stock} bot={bot.stock} store={inv}"
    )
    # El PRECIO del bot, la Store API y el renderizado del storefront coinciden.
    assert bot.price == price, f"Precio bot={bot.price} != store={price}"
    print("\n  -> Storefront, bot y Admin API comparten la MISMA fuente de verdad.")
