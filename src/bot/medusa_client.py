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
    variant_id: str = ""
    variant_count: int = 1  # cuantas variantes tiene el producto (color/talla)


@dataclass
class OrderInfo:
    display_id: int
    status: str
    total: int | None
    currency: str


@dataclass
class OrderLine:
    title: str
    quantity: int


@dataclass
class OrderDetail:
    id: str
    display_id: int
    status: str
    payment_status: str
    fulfillment_status: str
    total: int | None
    currency: str
    items: List[OrderLine]
    metadata: dict


class MedusaClient:
    """Acceso a Medusa. Lectura de catálogo/pedidos y operaciones de pedido.

    No inventa datos: toda cifra proviene de la API. Las operaciones de escritura
    (crear/confirmar/facturar/despachar) viven aquí pero las invoca el agente solo
    tras confirmación explícita del dueño (ver tools.py / brain.py).
    """

    def __init__(
        self,
        base_url: str | None = None,
        publishable_key: str | None = None,
        region_id: str | None = None,
        admin_token: str | None = None,
        admin_email: str | None = None,
        admin_password: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("MEDUSA_BACKEND_URL", "http://localhost:9001")).rstrip("/")
        self.publishable_key = publishable_key or os.getenv("MEDUSA_PUBLISHABLE_KEY", "")
        self.region_id = region_id or os.getenv("MEDUSA_REGION_ID", "")
        self.admin_token = admin_token or os.getenv("MEDUSA_ADMIN_TOKEN", "")
        # Credenciales para auto-login a la Admin API si no hay token fijo.
        self.admin_email = admin_email or os.getenv("MEDUSA_ADMIN_EMAIL", "")
        self.admin_password = admin_password or os.getenv("MEDUSA_ADMIN_PASSWORD", "")
        self.session = session or requests.Session()

    # ---- Store API (publishable key) ----
    def _store_headers(self) -> dict:
        return {"x-publishable-api-key": self.publishable_key}

    @staticmethod
    def _singularizar(query: str) -> str:
        """Heuristica simple es-CO: quita la 's' final de palabras largas.

        El buscador de Medusa no es plural-aware ('candados' no casa 'Candado').
        candados->candado, cascos->casco. No toca palabras cortas.
        """
        palabras = [
            w[:-1] if len(w) > 3 and w.lower().endswith("s") else w
            for w in query.split()
        ]
        return " ".join(palabras)

    def search_products(self, query: str, limit: int = 5) -> List[ProductInfo]:
        """Busca productos por texto (precio + stock REALES).

        Si no hay resultados y la consulta parece plural, reintenta en singular.
        """
        productos = self._search_raw(query, limit)
        if not productos:
            alt = self._singularizar(query)
            if alt and alt.lower() != (query or "").lower():
                productos = self._search_raw(alt, limit)
        return productos

    def _search_raw(self, query: str, limit: int = 5) -> List[ProductInfo]:
        return self._store_products({"q": query}, limit)

    def _store_products(self, extra: dict, limit: int) -> List[ProductInfo]:
        """GET /store/products con parametros extra (q, category_id[], ...) y parseo."""
        params = {
            "limit": str(limit),
            "fields": "id,title,*variants,+variants.calculated_price,+variants.inventory_quantity",
        }
        params.update(extra)
        if self.region_id:
            params["region_id"] = self.region_id
        resp = self.session.get(
            f"{self.base_url}/store/products",
            params=params,
            headers=self._store_headers(),
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        result: List[ProductInfo] = []
        for p in resp.json().get("products", []):
            variants = p.get("variants") or []
            v = variants[0] if variants else {}
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
                    variant_id=v.get("id") or "",
                    variant_count=len(variants),
                )
            )
        return result

    # ---- Categorias ----
    def list_categories(self) -> List[dict]:
        """Todas las categorias: {name, is_active}. Activas = publicas; inactivas =
        codigos internos del dueño (1-RK, 6-CL, PITILLOS...)."""
        resp = self._admin_request(
            "GET", "/admin/product-categories",
            params={"limit": "200", "fields": "id,name,is_active"},
        )
        return [
            {"id": c.get("id"), "name": c.get("name", ""), "is_active": bool(c.get("is_active"))}
            for c in resp.json().get("product_categories", [])
        ]

    def products_in_category(self, name: str, limit: int = 20) -> List[ProductInfo] | None:
        """Productos de una categoria PUBLICA (activa) por nombre. None si no existe."""
        cat = next(
            (c for c in self.list_categories()
             if c["is_active"] and c["name"].lower() == (name or "").strip().lower()),
            None,
        )
        if cat is None:
            return None
        return self._store_products({"category_id[]": cat["id"]}, limit)

    def products_by_codigo(self, codigo: str, max_total: int = 800) -> List[str]:
        """Titulos de los productos con ese codigo interno del dueño (metadata)."""
        codigo = (codigo or "").strip().upper()
        titulos: List[str] = []
        offset, page = 0, 200
        while offset < max_total:
            resp = self._admin_request(
                "GET", "/admin/products",
                params={"limit": str(page), "offset": str(offset), "fields": "title,metadata"},
            )
            prods = resp.json().get("products", [])
            for p in prods:
                if str((p.get("metadata") or {}).get("codigo_interno", "")).upper() == codigo:
                    titulos.append(p.get("title", ""))
            if len(prods) < page:
                break
            offset += page
        return titulos

    # ---- Admin API (token) ----
    def _login_admin(self) -> str:
        """Obtiene un JWT de la Admin API con email/password. Lo cachea en self.

        No inventa nada: si no hay credenciales o el login falla, lanza para que
        la capa de handlers responda "dato no disponible".
        """
        if not self.admin_email or not self.admin_password:
            raise RuntimeError("Sin credenciales admin (MEDUSA_ADMIN_EMAIL/PASSWORD).")
        resp = self.session.post(
            f"{self.base_url}/auth/user/emailpass",
            json={"email": self.admin_email, "password": self.admin_password},
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        token = resp.json().get("token")
        if not token:
            raise RuntimeError("Auth admin sin token.")
        self.admin_token = token
        return token

    def _admin_headers(self) -> dict:
        if not self.admin_token:
            self._login_admin()
        return {"Authorization": f"Bearer {self.admin_token}"}

    def _admin_request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Llama a la Admin API con auto-login y un reintento si el token caduca (401)."""
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        resp = self.session.request(method, url, headers=self._admin_headers(), **kwargs)
        if resp.status_code == 401 and self.admin_email and self.admin_password:
            self._login_admin()  # token vencido: re-login y un reintento
            resp = self.session.request(method, url, headers=self._admin_headers(), **kwargs)
        resp.raise_for_status()
        return resp

    @staticmethod
    def _to_int(v) -> int | None:
        return int(v) if isinstance(v, (int, float)) else None

    def list_orders(self, limit: int = 5) -> List[OrderInfo]:
        """Devuelve los ultimos pedidos REALES desde la Admin API."""
        resp = self._admin_request(
            "GET", "/admin/orders",
            params={"limit": str(limit), "fields": "display_id,status,total,currency_code"},
        )
        result: List[OrderInfo] = []
        for o in resp.json().get("orders", []):
            result.append(
                OrderInfo(
                    display_id=o.get("display_id"),
                    status=o.get("status", ""),
                    total=self._to_int(o.get("total")),
                    currency=(o.get("currency_code") or "cop").upper(),
                )
            )
        return result

    def get_order(self, display_id: int, max_search: int = 2000, page: int = 100) -> OrderDetail | None:
        """Detalle REAL de un pedido por su numero visible (display_id).

        Pagina la Admin API hasta encontrar el display_id (NO solo entre los mas
        recientes) y devuelve None si no existe (no inventa). Antes miraba solo los
        50 pedidos recientes: pasando 50 pedidos, cualquier pedido viejo se volvia
        "no encontrado" en silencio (consultar/confirmar/facturar/despachar). `max_search`
        acota el barrido para no recorrer indefinidamente si el numero no existe.
        """
        fields = (
            "id,display_id,status,payment_status,fulfillment_status,"
            "total,currency_code,metadata,items.title,items.quantity"
        )
        offset = 0
        while offset < max_search:
            resp = self._admin_request(
                "GET", "/admin/orders",
                params={"limit": str(page), "offset": str(offset), "fields": fields},
            )
            orders = resp.json().get("orders", [])
            for o in orders:
                if o.get("display_id") == display_id:
                    items = [
                        OrderLine(title=it.get("title", ""), quantity=int(it.get("quantity") or 0))
                        for it in (o.get("items") or [])
                    ]
                    return OrderDetail(
                        id=o.get("id", ""),
                        display_id=o.get("display_id"),
                        status=o.get("status", ""),
                        payment_status=o.get("payment_status", ""),
                        fulfillment_status=o.get("fulfillment_status", ""),
                        total=self._to_int(o.get("total")),
                        currency=(o.get("currency_code") or "cop").upper(),
                        items=items,
                        metadata=o.get("metadata") or {},
                    )
            if len(orders) < page:
                break  # ultima pagina: no hay mas pedidos que revisar
            offset += page
        return None

    # ---- Operaciones de escritura (las invoca el agente tras confirmacion) ----
    def create_order(self, items: list, email: str | None = None) -> OrderDetail | None:
        """Crea un pedido: draft-order y conversion inmediata a order (queda pending).

        items: [{"variant_id": str, "quantity": int}, ...]. Region y sales channel
        salen del entorno (MEDUSA_REGION_ID, MEDUSA_SALES_CHANNEL_ID).
        """
        region_id = self.region_id or os.getenv("MEDUSA_REGION_ID", "")
        sales_channel_id = os.getenv("MEDUSA_SALES_CHANNEL_ID", "")
        if not region_id or not sales_channel_id:
            raise RuntimeError("Falta MEDUSA_REGION_ID o MEDUSA_SALES_CHANNEL_ID.")
        payload = {
            "email": email or "cliente.mostrador@tiendaciclismo.co",
            "region_id": region_id,
            "sales_channel_id": sales_channel_id,
            "items": items,
        }
        draft = self._admin_request("POST", "/admin/draft-orders", json=payload).json().get("draft_order") or {}
        draft_id = draft.get("id")
        if not draft_id:
            raise RuntimeError("No se pudo crear el borrador del pedido.")
        self._admin_request("POST", f"/admin/draft-orders/{draft_id}/convert-to-order", json={})
        return self.get_order(draft.get("display_id"))

    def update_order_metadata(self, order_id: str, nuevos: dict, actuales: dict | None = None) -> dict:
        """Fusiona metadata (no pisa lo existente) y la guarda en el pedido."""
        fusion = dict(actuales or {})
        fusion.update(nuevos)
        self._admin_request("POST", f"/admin/orders/{order_id}", json={"metadata": fusion})
        return fusion
