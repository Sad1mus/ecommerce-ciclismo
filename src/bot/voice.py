"""Pipeline de voz: audio -> texto (Whisper) -> comando -> respuesta.

El transcriptor (STT) esta detras del protocolo `Transcriber`, asi en los tests
se inyecta un transcriptor falso y NO se necesita OPENAI_API_KEY ni modelos
reales. En produccion se usa WhisperTranscriber (Whisper via API de OpenAI).

ANTI-ALUCINACION: si la transcripcion falla, NO se adivina el comando; se
responde un mensaje claro. Los datos de la respuesta salen siempre de Medusa
a traves de los handlers.
"""
from __future__ import annotations

import os
from typing import Protocol, Tuple

import handlers
from formatting import DATO_NO_DISPONIBLE
from medusa_client import MedusaClient

AUDIO_NO_ENTENDIDO = (
    "No fue posible entender el audio. Repite el comando, por ejemplo: "
    "stock candado, precio bomba, o pedidos."
)
COMANDO_DESCONOCIDO = (
    "Comando de voz no reconocido. Comandos: stock <producto>, "
    "precio <producto>, pedidos."
)


class Transcriber(Protocol):
    def transcribe(self, audio: bytes) -> str:  # pragma: no cover - interfaz
        ...


def route_command(texto: str) -> Tuple[str, str]:
    """Convierte texto libre en (comando, argumento). No inventa datos."""
    t = (texto or "").strip().lower()
    if not t:
        return ("desconocido", "")
    # quitar la palabra clave para quedarnos con el argumento
    if "precio" in t or "cuesta" in t or "vale" in t:
        arg = t.replace("precio", "").replace("cuesta", "").replace("vale", "")
        arg = arg.replace("de", " ").replace("cuanto", "").strip()
        return ("precio", arg)
    if "pedido" in t or "orden" in t:
        return ("pedidos", "")
    if "stock" in t or "disponib" in t or "inventario" in t or "hay" in t:
        for kw in ("stock", "disponibilidad", "disponible", "inventario", "cuanto", "hay", "de"):
            t = t.replace(kw, " ")
        return ("stock", t.strip())
    return ("desconocido", "")


class VoicePipeline:
    def __init__(self, transcriber: Transcriber, client: MedusaClient) -> None:
        self.transcriber = transcriber
        self.client = client

    def process(self, audio: bytes) -> str:
        try:
            texto = self.transcriber.transcribe(audio)
        except Exception:
            return AUDIO_NO_ENTENDIDO
        if not texto or not texto.strip():
            return AUDIO_NO_ENTENDIDO

        comando, arg = route_command(texto)
        if comando == "stock":
            return handlers.handle_stock(self.client, arg)
        if comando == "precio":
            return handlers.handle_precio(self.client, arg)
        if comando == "pedidos":
            return handlers.handle_pedidos(self.client)
        return COMANDO_DESCONOCIDO


class WhisperTranscriber:
    """STT real con Whisper (API de OpenAI). Import diferido; no se usa en tests.

    Requiere OPENAI_API_KEY en el entorno (nunca en el repo).
    """

    def __init__(self, model: str = "whisper-1") -> None:
        self.model = model

    def transcribe(self, audio: bytes) -> str:  # pragma: no cover - requiere red/clave
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Falta OPENAI_API_KEY para Whisper.")
        from openai import OpenAI  # import diferido

        client = OpenAI(api_key=api_key)
        import io

        buf = io.BytesIO(audio)
        buf.name = "audio.ogg"
        resp = client.audio.transcriptions.create(model=self.model, file=buf)
        return resp.text
