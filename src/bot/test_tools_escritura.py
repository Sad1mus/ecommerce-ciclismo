"""Tests de las herramientas de ESCRITURA: la guarda de confirmacion y la mutacion."""
from medusa_client import OrderDetail, OrderLine, ProductInfo
from testing_fakes import FakeClient
import tools

PRODS = [ProductInfo(title="Candado espiral", sku="CL1", price=14500, currency="COP", stock=8, variant_id="var_1")]


def _detalle(numero=1001, metadata=None):
    return OrderDetail(
        id=f"order_{numero}", display_id=numero, status="pending", payment_status="captured",
        fulfillment_status="not_fulfilled", total=29000, currency="COP",
        items=[OrderLine(title="Candado espiral", quantity=2)], metadata=metadata or {},
    )


# ---- crear_pedido ----
def test_crear_pedido_sin_confirmar_no_muta():
    c = FakeClient(productos=PRODS)
    out = tools.crear_pedido(c, "candado", cantidad=2)
    assert "CONFIRMACION" in out and "Candado espiral" in out
    assert c.escrituras == []  # NO creo nada


def test_crear_pedido_confirmado_muta():
    c = FakeClient(productos=PRODS)
    out = tools.crear_pedido(c, "candado", cantidad=2, confirmado=True)
    assert "creado" in out.lower()
    assert c.escrituras and c.escrituras[0][0] == "create_order"


def test_crear_pedido_sin_resultados_no_muta():
    c = FakeClient(productos=[])
    out = tools.crear_pedido(c, "xyz", confirmado=True)
    assert "Sin resultados" in out and c.escrituras == []


# ---- facturar ----
def test_facturar_sin_confirmar_no_muta():
    c = FakeClient(detalles={1001: _detalle()})
    out = tools.facturar_pedido(c, 1001)
    assert "CONFIRMACION" in out and c.escrituras == []


def test_facturar_confirmado_genera_numero():
    c = FakeClient(detalles={1001: _detalle()})
    out = tools.facturar_pedido(c, 1001, confirmado=True)
    assert "F-01001" in out
    assert c.escrituras and c.escrituras[0][2].get("factura_numero") == "F-01001"


def test_facturar_ya_facturado_no_remuta():
    c = FakeClient(detalles={1001: _detalle(metadata={"factura_numero": "F-01001"})})
    out = tools.facturar_pedido(c, 1001, confirmado=True)
    assert "ya tiene factura" in out and c.escrituras == []


def test_facturar_pedido_inexistente():
    out = tools.facturar_pedido(FakeClient(detalles={}), 7777, confirmado=True)
    assert "7777" in out and "no" in out.lower()


# ---- marcar_transportadora ----
def test_despacho_sin_confirmar_no_muta():
    c = FakeClient(detalles={1001: _detalle()})
    out = tools.marcar_transportadora(c, 1001, "Servientrega", "ABC123")
    assert "CONFIRMACION" in out and "Servientrega" in out and c.escrituras == []


def test_despacho_confirmado_muta():
    c = FakeClient(detalles={1001: _detalle()})
    out = tools.marcar_transportadora(c, 1001, "Servientrega", "ABC123", confirmado=True)
    assert "despachado" in out.lower() and "Servientrega" in out
    meta = c.escrituras[0][2]
    assert meta["transportadora"] == "Servientrega" and meta["estado_operativo"] == "despachado"


def test_despacho_sin_empresa_pregunta():
    out = tools.marcar_transportadora(FakeClient(detalles={1001: _detalle()}), 1001, "")
    assert "transportadora" in out.lower()


# ---- confirmar y empaque ----
def test_confirmar_pedido_flujo():
    c = FakeClient(detalles={1001: _detalle()})
    assert "CONFIRMACION" in tools.confirmar_pedido(c, 1001)
    out = tools.confirmar_pedido(c, 1001, confirmado=True)
    assert "confirmado" in out.lower()
    assert c.escrituras[0][2]["estado_operativo"] == "confirmado"


def test_plantilla_empaque_lista_items():
    out = tools.plantilla_empaque(FakeClient(detalles={1001: _detalle()}), 1001)
    assert "Empaque del pedido 1001" in out and "2 x Candado espiral" in out
