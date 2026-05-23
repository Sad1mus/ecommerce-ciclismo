"""Tests del cerebro conversacional con LLM y Medusa MOCKEADOS.

No requieren GROQ_API_KEY ni red: el LLM es un doble que devuelve respuestas
programadas (texto o llamadas a herramientas).
"""
from brain import Brain
from formatting import is_screen_reader_safe
from medusa_client import OrderDetail, OrderLine, ProductInfo
from testing_fakes import (
    FailingClient,
    FailingLLM,
    FakeClient,
    FakeLLM,
    msg_texto,
    msg_tool_call,
)

PRODS = [ProductInfo(title="Candado espiral", sku="CL1", price=14500, currency="COP", stock=8)]


def test_flujo_consulta_usa_dato_real_de_la_tool():
    # El LLM decide llamar a la herramienta; el dato sale del cliente, no del LLM.
    llm = FakeLLM([
        msg_tool_call("consultar_producto", {"consulta": "candado"}),
        msg_texto("Hay 8 candados espiral a 14.500 pesos."),
    ])
    brain = Brain(llm, FakeClient(productos=PRODS))
    out = brain.handle("chat1", "¿cómo vamos de candados?")
    assert out == "Hay 8 candados espiral a 14.500 pesos."
    assert is_screen_reader_safe(out)
    # El resultado real de la tool se inyecto en el historial (segunda llamada al LLM).
    segunda_llamada = llm.calls[1]
    tool_msgs = [m for m in segunda_llamada if m.get("role") == "tool"]
    assert tool_msgs and "Candado espiral" in tool_msgs[0]["content"]


def test_respuesta_directa_sin_tool():
    llm = FakeLLM([msg_texto("Claro, dime el nombre del producto.")])
    out = Brain(llm, FakeClient()).handle("c", "hola")
    assert out == "Claro, dime el nombre del producto."


def test_llm_caido_no_inventa():
    out = Brain(FailingLLM(), FakeClient(productos=PRODS)).handle("c", "stock de candado")
    assert "no puedo procesar" in out.lower()
    assert not any(ch.isdigit() for ch in out)  # nada de cifras inventadas


def test_consulta_pedido_por_conversacion():
    det = OrderDetail(
        id="o1", display_id=1001, status="pending", payment_status="captured",
        fulfillment_status="not_fulfilled", total=26000, currency="COP",
        items=[OrderLine(title="Candado espiral", quantity=2)], metadata={},
    )
    llm = FakeLLM([
        msg_tool_call("consultar_pedido", {"numero": 1001}),
        msg_texto("El pedido 1001 esta pendiente, total 26.000 pesos."),
    ])
    out = Brain(llm, FakeClient(detalles={1001: det})).handle("c", "qué pasó con el pedido 1001")
    assert "1001" in out


def test_tool_desconocida_no_rompe():
    llm = FakeLLM([
        msg_tool_call("herramienta_fantasma", {}),
        msg_texto("Listo."),
    ])
    out = Brain(llm, FakeClient()).handle("c", "haz algo raro")
    assert out == "Listo."


def test_memoria_y_reset_por_chat():
    llm = FakeLLM([msg_texto("uno"), msg_texto("dos")])
    brain = Brain(llm, FakeClient())
    brain.handle("c", "primero")
    brain.handle("c", "segundo")
    # El historial acumula: system + 2 user + 2 assistant = 5
    assert len(brain._histories["c"]) == 5
    brain.reset("c")
    assert "c" not in brain._histories


def test_tope_de_rondas_de_tool_no_cuelga():
    # El LLM siempre pide tool: el brain corta y responde sin colgarse.
    llm = FakeLLM([msg_tool_call("consultar_producto", {"consulta": "x"})] * 20)
    out = Brain(llm, FakeClient(productos=PRODS)).handle("c", "loop")
    assert "no pude completar" in out.lower()
