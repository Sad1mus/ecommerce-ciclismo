"""Cliente de la API de Medusa para el bot.

REGLA ANTI-ALUCINACION del proyecto: el stock, los precios y los pedidos
SIEMPRE provienen de Medusa (Store API / Admin API). Este modulo solo lee de la
API; nunca inventa, estima ni rellena datos. Si una llamada falla, propaga la
excepcion para que la capa de handlers responda "dato no disponible" en vez de
fabricar una respuesta.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

import requests

DEFAULT_TIMEOUT = 10


@dataclass
class ProductInfo:
    title: str
    sku: str
    price: int | None
    currency: str
    stock: int | None


@dataclass
class OrderInfo:
    display_id: int
    status: str
    total: int | None
    currency: str


class MedusaClient:
    """Acceso de solo-lectura a Medusa. No cachea ni inventa datos."""

    def __init__(
        self,
        base_url: str | None = None,
        publishable_key: str | None = None,
        region_id: str | None = None,
        admin_token: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("MEDUSA_BACKEND_URL", "http://localhost:9001")).rstrip("/")
        self.publishable_key = publishable_key or os.getenv("MEDUSA_PUBLISHABLE_KEY", "")
        self.region_id = region_id or os.getenv("MEDUSA_REGION_ID", "")
        self.admin_token = admin_token or os.getenv("MEDUSA_ADMIN_TOKEN", "")
        self.session = session or requests.Session()

    # ---- Store API (publishable key) ----
    def _store_headers(self) -> dict:
        return {"x-publishable-api-key": self.publishable_key}

    def search_products(self, query: str, limit: int = 5) -> List[ProductInfo]:
        """Busca productos por texto y devuelve precio + stock REALES de la API."""
        params = {
            "q": query,
            "limit": str(limit),
            "fields": "id,title,*variants,+variants.calculated_price,+variants.inventory_quantity",
        }
        if self.region_id:
            params["region_id"] = self.region_id
        resp = self.session.get(
            f"{self.base_url}/store/products",
            params=params,
            headers=self._store_headers(),
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        result: List[ProductInfo] = []
        for p in data.get("products", []):
            variants = p.get("variants") or [{}]
            v = variants[0]
            cp = v.get("calculated_price") or {}
            amount = cp.get("calculated_amount")
            result.append(
                ProductInfo(
                    title=p.get("title", ""),
                    sku=v.get("sku") or "",
                    price=int(amount) if isinstance(amount, (int, float)) else None,
                    currency=(cp.get("currency_code") or "cop").upper(),
                    stock=v.get("inventory_quantity")
                    if isinstance(v.get("inventory_quantity"), int)
                    else None,
                )
            )
        return result

    # ---- Admin API (token) ----
    def _admin_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.admin_token}"}

    def list_orders(self, limit: int = 5) -> List[OrderInfo]:
        """Devuelve los ultimos pedidos REALES desde la Admin API."""
        resp = self.session.get(
            f"{self.base_url}/admin/orders",
            params={"limit": str(limit), "fields": "display_id,status,total,currency_code"},
            headers=self._admin_headers(),
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        result: List[OrderInfo] = []
        for o in data.get("orders", []):
            total = o.get("total")
            result.append(
                OrderInfo(
                    display_id=o.get("display_id"),
                    status=o.get("status", ""),
                    total=int(total) if isinstance(total, (int, float)) else None,
                    currency=(o.get("currency_code") or "cop").upper(),
                )
            )
        return result
