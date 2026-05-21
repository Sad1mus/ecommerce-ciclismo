"""Tests del pipeline de voz con STT (Whisper) MOCKEADO.

No requieren OPENAI_API_KEY ni audio real: el transcriptor es un doble.
"""
from formatting import has_emoji, is_screen_reader_safe
from medusa_client import ProductInfo, OrderInfo
from testing_fakes import FailingTranscriber, FakeClient, FakeTranscriber
from voice import (
    AUDIO_NO_ENTENDIDO,
    COMANDO_DESCONOCIDO,
    VoicePipeline,
    route_command,
)

PRODS = [ProductInfo(title="Candado espiral", sku="CL1", price=14500, currency="COP", stock=8)]


# ---- enrutado de texto a comando ----
def test_route_stock():
    assert route_command("stock candado")[0] == "stock"
    assert "candado" in route_command("cuanto stock hay de candado")[1]


def test_route_precio():
    cmd, arg = route_command("precio bomba")
    assert cmd == "precio"
    assert "bomba" in arg


def test_route_pedidos():
    assert route_command("muestrame los pedidos")[0] == "pedidos"


def test_route_desconocido():
    assert route_command("hola que tal")[0] == "desconocido"


# ---- pipeline completo audio->texto->comando->respuesta ----
def test_pipeline_voz_devuelve_stock_real():
    pipe = VoicePipeline(FakeTranscriber("stock candado"), FakeClient(productos=PRODS))
    salida = pipe.process(b"audio-falso")
    assert "8 unidades" in salida  # el dato sale del cliente, no del audio
    assert is_screen_reader_safe(salida)


def test_pipeline_voz_precio_real():
    pipe = VoicePipeline(FakeTranscriber("precio candado"), FakeClient(productos=PRODS))
    salida = pipe.process(b"audio")
    assert "14.500" in salida


def test_pipeline_stt_falla_no_inventa():
    pipe = VoicePipeline(FailingTranscriber(), FakeClient(productos=PRODS))
    salida = pipe.process(b"audio-corrupto")
    assert salida == AUDIO_NO_ENTENDIDO
    assert not any(c.isdigit() for c in salida)


def test_pipeline_transcripcion_vacia():
    pipe = VoicePipeline(FakeTranscriber("   "), FakeClient(productos=PRODS))
    assert pipe.process(b"x") == AUDIO_NO_ENTENDIDO


def test_pipeline_comando_desconocido():
    pipe = VoicePipeline(FakeTranscriber("buenos dias"), FakeClient(productos=PRODS))
    assert pipe.process(b"x") == COMANDO_DESCONOCIDO


def test_pipeline_pedidos_por_voz():
    pipe = VoicePipeline(
        FakeTranscriber("pedidos"),
        FakeClient(pedidos=[OrderInfo(1001, "completed", 34000, "COP")]),
    )
    salida = pipe.process(b"x")
    assert "1001" in salida
    assert not has_emoji(salida)
