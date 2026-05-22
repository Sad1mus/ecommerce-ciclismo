"""Fixtures compartidos por los tests del bot."""
import os
import pathlib

import pytest
import requests

from medusa_client import OrderInfo, ProductInfo


@pytest.fixture
def productos_demo():
    return [
        ProductInfo(title="Candado espiral", sku="CL1", price=14500, currency="COP", stock=8),
        ProductInfo(title="Candado clave", sku="CL2", price=18500, currency="COP", stock=2),
        ProductInfo(title="Bomba mini", sku="B1", price=18500, currency="COP", stock=None),
    ]


@pytest.fixture
def pedidos_demo():
    return [
        OrderInfo(display_id=1001, status="completed", total=34000, currency="COP"),
        OrderInfo(display_id=1002, status="pending", total=52000, currency="COP"),
    ]


# ---------------------------------------------------------------------------
# Soporte para los tests de INTEGRACION (stack REAL, sin mocks).
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _load_env_file(path: pathlib.Path) -> None:
    """Carga variables KEY=VALUE de un fichero .env a os.environ (sin dependencias).

    No pisa variables ya presentes en el entorno (setdefault), para que el usuario
    pueda sobreescribir por export. No commitea nada: solo lee ficheros locales.
    """
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


@pytest.fixture(scope="session")
def medusa_cfg():
    """Resuelve la config del Medusa REAL y verifica que el stack este vivo.

    Si el backend no responde, hace SKIP (no falla): asi `-m integration` no
    rompe en entornos sin stack. La region COP se resuelve dinamicamente desde la
    Store API para no depender de un id fijo (puede cambiar al re-sembrar la DB).
    """
    _load_env_file(_REPO_ROOT / ".env")
    if not os.environ.get("MEDUSA_PUBLISHABLE_KEY"):
        sf = _REPO_ROOT / "src" / "storefront" / ".env.local"
        if sf.exists():
            for raw in sf.read_text().splitlines():
                if raw.startswith("NEXT_PUBLIC_MEDUSA_PUBLISHABLE_KEY="):
                    os.environ["MEDUSA_PUBLISHABLE_KEY"] = raw.split("=", 1)[1].strip()

    base = os.environ.get("MEDUSA_BACKEND_URL", "http://localhost:9001").rstrip("/")
    pk = os.environ.get("MEDUSA_PUBLISHABLE_KEY", "")
    if not pk:
        pytest.skip("Falta MEDUSA_PUBLISHABLE_KEY (stack real no configurado)")
    try:
        health = requests.get(f"{base}/health", timeout=5)
    except requests.RequestException as exc:
        pytest.skip(f"Medusa no responde en {base}: {exc}")
    if health.status_code != 200:
        pytest.skip(f"Medusa /health = {health.status_code}")

    regions = requests.get(
        f"{base}/store/regions", headers={"x-publishable-api-key": pk}, timeout=10
    )
    regions.raise_for_status()
    region_id = next(
        (r["id"] for r in regions.json().get("regions", []) if r.get("currency_code") == "cop"),
        None,
    )
    if not region_id:
        pytest.skip("No hay region COP en la Store API")
    # El MedusaClient lee MEDUSA_REGION_ID del entorno: lo fijamos al COP real.
    os.environ["MEDUSA_REGION_ID"] = region_id
    return {"base": base, "pk": pk, "region_id": region_id}


@pytest.fixture(scope="session")
def admin_token(medusa_cfg):
    """Token de la Admin API autenticando con credenciales de DEV (env).

    Hace SKIP si no hay credenciales: el E2E sigue siendo ejecutable sin Admin.
    """
    email = os.environ.get("MEDUSA_ADMIN_EMAIL")
    password = os.environ.get("MEDUSA_ADMIN_PASSWORD")
    if not email or not password:
        pytest.skip("Sin MEDUSA_ADMIN_EMAIL/PASSWORD para la Admin API")
    resp = requests.post(
        f"{medusa_cfg['base']}/auth/user/emailpass",
        json={"email": email, "password": password},
        timeout=10,
    )
    if resp.status_code != 200:
        pytest.skip(f"Auth admin fallida ({resp.status_code})")
    token = resp.json().get("token")
    if not token:
        pytest.skip("Auth admin sin token")
    return token


def admin_stocked_quantity(cfg, token, query):
    """stocked_quantity REAL desde la Admin API para el primer variante que matchee.

    Devuelve dict {sku: stocked_quantity} de los location levels. Esta es la
    'fuente de verdad' del inventario en la DB (lo que la bodega tiene fisicamente).
    """
    resp = requests.get(
        f"{cfg['base']}/admin/products",
        params={
            "q": query,
            "limit": "5",
            "fields": "title,*variants,*variants.inventory_items.inventory.location_levels",
        },
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    resp.raise_for_status()
    out = {}
    for p in resp.json().get("products", []):
        for v in p.get("variants", []) or []:
            sku = v.get("sku")
            if not sku:
                continue
            total = 0
            for ii in v.get("inventory_items", []) or []:
                inv = ii.get("inventory") or {}
                for lvl in inv.get("location_levels", []) or []:
                    total += int(lvl.get("stocked_quantity") or 0)
            out[sku] = total
    return out


def store_products(cfg, limit=20, query=None):
    """Llamada CRUDA e independiente a la Store API: la 'fuente de verdad' contra
    la que comparamos al bot. Devuelve la lista cruda de productos con precio+stock.
    """
    params = {
        "limit": str(limit),
        "region_id": cfg["region_id"],
        "fields": "id,title,handle,status,*variants,+variants.calculated_price,+variants.inventory_quantity",
    }
    if query:
        params["q"] = query
    resp = requests.get(
        f"{cfg['base']}/store/products",
        params=params,
        headers={"x-publishable-api-key": cfg["pk"]},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json().get("products", [])
