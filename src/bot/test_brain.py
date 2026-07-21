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
    # El historial acumula (via store): system + 2 user + 2 assistant = 5
    assert len(brain.store.load("c")) == 5
    brain.reset("c")
    assert brain.store.load("c") is None


def test_tope_de_rondas_de_tool_no_cuelga():
    # El LLM siempre pide tool: el brain corta y responde sin colgarse.
    llm = FakeLLM([msg_tool_call("consultar_producto", {"consulta": "x"})] * 20)
    out = Brain(llm, FakeClient(productos=PRODS)).handle("c", "loop")
    assert "no pude completar" in out.lower()


def _detalle_pedido(numero=1001):
    return OrderDetail(
        id=f"o{numero}", display_id=numero, status="pending", payment_status="captured",
        fulfillment_status="not_fulfilled", total=29000, currency="COP",
        items=[OrderLine(title="Candado espiral", quantity=2)], metadata={},
    )


def test_auditoria_registra_escritura_no_lectura(caplog):
    import logging

    # Escritura (facturar confirmado) -> debe dejar rastro en el logger bot.audit.
    llm = FakeLLM([
        msg_tool_call("facturar_pedido", {"numero": 1001, "confirmado": True}),
        msg_texto("Facturado."),
    ])
    brain = Brain(llm, FakeClient(detalles={1001: _detalle_pedido()}))
    with caplog.at_level(logging.INFO, logger="bot.audit"):
        brain.handle("chat9", "factura el 1001")
    registros = [r for r in caplog.records if r.name == "bot.audit"]
    assert registros, "una operacion de escritura debe auditarse"
    msg = registros[0].getMessage()
    assert "chat9" in msg and "facturar_pedido" in msg

    # Lectura (consultar_producto) -> NO debe generar auditoria.
    caplog.clear()
    llm2 = FakeLLM([
        msg_tool_call("consultar_producto", {"consulta": "candado"}),
        msg_texto("Hay stock."),
    ])
    brain2 = Brain(llm2, FakeClient(productos=PRODS))
    with caplog.at_level(logging.INFO, logger="bot.audit"):
        brain2.handle("chat9", "cuantos candados hay")
    assert [r for r in caplog.records if r.name == "bot.audit"] == []


def test_rate_limit_corta_antes_de_llamar_al_llm():
    from ratelimit import RateLimiter

    llm = FakeLLM([msg_texto("uno"), msg_texto("dos")])
    # Cupo 1 por ventana: el segundo mensaje se corta SIN consumir al LLM.
    brain = Brain(llm, FakeClient(), limiter=RateLimiter(max_calls=1, window_seconds=60, clock=lambda: 1000.0))
    primero = brain.handle("c", "hola")
    segundo = brain.handle("c", "otra vez")
    assert primero == "uno"
    assert "muchos mensajes" in segundo.lower()
    assert len(llm.calls) == 1  # el LLM solo se llamo una vez (el 2do no lo toco)
