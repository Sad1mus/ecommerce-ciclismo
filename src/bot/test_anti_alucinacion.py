"""Suite ANTI-ALUCINACIÓN E2E contra el stack REAL (sin mocks).

Garantías que verifica de punta a punta:
  (a) stock y precio que reportan bot y storefront coinciden EXACTAMENTE con la DB
      (Admin API) para >=5 SKUs reales.
  (b) ante un fallo real de la API (backend inalcanzable), el bot responde
      "dato no disponible" — NO inventa cifras.
  (c) los 28 productos en borrador (precio estimado, sin confirmar) NO son
      comprables en el storefront (no los expone la Store API).

Requiere el stack vivo (scripts/dev-up.sh) y credenciales admin de dev.
    python -m pytest -q -m integration
"""
from __future__ import annotations

import os

import pytest
import requests

import handlers
from conftest import (
    admin_products_by_status,
    admin_stocked_quantity,
    store_product_count_by_handle,
    store_products,
)
from formatting import DATO_NO_DISPONIBLE
from medusa_client import MedusaClient

pytestmark = pytest.mark.integration


def _storefront_price_ok(sess, sf_base, handle, price):
    """True si la página real del producto renderiza el precio crudo (data-value)."""
    page = sess.get(f"{sf_base}/co/products/{handle}", timeout=30)
    return page.status_code == 200 and f'data-value="{price}"' in page.text


# ---------- (a) stock+precio: Admin API == bot == Store API == storefront ----------
def test_a_stock_y_precio_coinciden_para_5_skus(medusa_cfg, admin_token):
    # Pool pequeño (sólo necesitamos 5): así no saturamos a Medusa con 40 búsquedas.
    candidatos = []
    for p in store_products(medusa_cfg, limit=10):
        v = (p.get("variants") or [{}])[0]
        inv, sku = v.get("inventory_quantity"), v.get("sku")
        price = (v.get("calculated_price") or {}).get("calculated_amount")
        if sku and p.get("handle") and isinstance(inv, int) and isinstance(price, (int, float)):
            candidatos.append({"title": p["title"], "handle": p["handle"], "sku": sku,
                               "inv": inv, "price": int(price)})

    client = MedusaClient()
    sf_base = os.environ.get("STOREFRONT_URL", "http://localhost:8000").rstrip("/")
    sess = requests.Session()
    sess.get(f"{sf_base}/co", timeout=30)  # primer hit: fija la cookie (evita 307 por ficha)

    verificados = 0
    print("\n  SKU            | DB(admin) | bot | StoreAPI | precio(bot=API=storefront)")
    print("  ---------------+-----------+-----+----------+---------------------------")
    for c in candidatos:
        # El bot busca por título contra el Medusa real; reintenta una vez si hay timeout.
        try:
            infos = client.search_products(c["title"], limit=10)
        except requests.RequestException:
            infos = client.search_products(c["title"], limit=10)
        bot = next((i for i in infos if i.sku == c["sku"]), None)
        if bot is None:
            continue
        admin_stock = admin_stocked_quantity(medusa_cfg, admin_token, c["title"]).get(c["sku"])
        if admin_stock is None:
            continue

        assert admin_stock == bot.stock == c["inv"], (
            f"{c['sku']} stock: admin={admin_stock} bot={bot.stock} store={c['inv']}"
        )
        assert bot.price == c["price"], f"{c['sku']} precio bot={bot.price} != store={c['price']}"
        assert _storefront_price_ok(sess, sf_base, c["handle"], c["price"]), (
            f"{c['sku']}: el storefront no renderiza el precio {c['price']}"
        )
        print(f"  {c['sku']:<14} | {admin_stock:>9} | {bot.stock:>3} | {c['inv']:>8} | {c['price']} (storefront OK)")
        verificados += 1
        if verificados >= 5:
            break

    assert verificados >= 5, f"Solo se verificaron {verificados} SKUs (se piden >=5)"
    print(f"\n  -> {verificados} SKUs: DB == bot == Store API == storefront (sin alucinación).")


# ---------- (b) fallo REAL de la API -> el bot no inventa ----------
def test_b_api_caida_el_bot_no_inventa(medusa_cfg):
    # Backend inalcanzable (puerto muerto): fallo de red REAL, no un mock.
    caido = MedusaClient(base_url="http://127.0.0.1:9", publishable_key="x", region_id="x")
    salida_stock = handlers.handle_stock(caido, "candado")
    salida_precio = handlers.handle_precio(caido, "candado")
    print(f"\n  API caída -> /stock  : {salida_stock!r}")
    print(f"  API caída -> /precio : {salida_precio!r}")
    assert salida_stock == DATO_NO_DISPONIBLE
    assert salida_precio == DATO_NO_DISPONIBLE
    # No inventa: ni dígitos ni símbolo de precio.
    assert not any(ch.isdigit() for ch in salida_stock)
    assert "$" not in salida_precio
    print("  -> El bot responde 'dato no disponible' y NO fabrica cifras.")


# ---------- (c) los 28 borradores NO son comprables ----------
def test_c_borradores_no_comprables(medusa_cfg, admin_token):
    drafts = admin_products_by_status(medusa_cfg, admin_token, "draft")
    print(f"\n  Borradores (Admin API, status=draft): {len(drafts)}")
    assert len(drafts) == 28, f"Se esperaban 28 borradores, hay {len(drafts)}"

    # Ninguno aparece como comprable en la Store API (lo que ve el storefront/bot).
    expuestos = [d["handle"] for d in drafts
                 if d.get("handle") and store_product_count_by_handle(medusa_cfg, d["handle"]) > 0]
    assert not expuestos, f"Borradores comprables vía Store API: {expuestos}"
    print(f"  -> Los {len(drafts)} borradores NO los expone la Store API (count=0 c/u).")

    # Y la página del storefront de un borrador NO es una ficha comprable (no 200).
    sf_base = os.environ.get("STOREFRONT_URL", "http://localhost:8000").rstrip("/")
    muestra = next((d["handle"] for d in drafts if d.get("handle")), None)
    if muestra:
        sess = requests.Session()
        code = sess.get(f"{sf_base}/co/products/{muestra}", timeout=30).status_code
        print(f"  -> Storefront /co/products/{muestra} -> HTTP {code} (no es 200 comprable).")
        assert code != 200, f"El borrador {muestra} se renderiza como ficha comprable (200)"
