"""Pipeline de voz: audio -> texto (Whisper) -> comando -> respuesta.

El transcriptor (STT) esta detras del protocolo `Transcriber`, asi en los tests
se inyecta un transcriptor falso y NO se necesita ninguna API key ni modelos
reales. En produccion el STT por defecto es Groq (Whisper large-v3, capa
gratuita y compatible con la API de OpenAI); si solo hay OPENAI_API_KEY se usa
Whisper via OpenAI. Ver `build_transcriber()`.

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


class _OpenAICompatTranscriber:
    """Base STT contra cualquier endpoint compatible con la API de OpenAI.

    Groq y OpenAI comparten el mismo SDK; solo cambian base_url, modelo y la
    variable de entorno con la clave. Import diferido: no se usa en tests.
    """

    env_var = "OPENAI_API_KEY"
    base_url: str | None = None
    default_model = "whisper-1"

    def __init__(self, model: str | None = None) -> None:
        self.model = model or self.default_model

    def transcribe(self, audio: bytes) -> str:  # pragma: no cover - requiere red/clave
        api_key = os.getenv(self.env_var)
        if not api_key:
            raise RuntimeError(f"Falta {self.env_var} para el STT.")
        from openai import OpenAI  # import diferido
        import io

        client = OpenAI(api_key=api_key, base_url=self.base_url)
        buf = io.BytesIO(audio)
        buf.name = "audio.ogg"
        resp = client.audio.transcriptions.create(model=self.model, file=buf)
        return resp.text


class GroqTranscriber(_OpenAICompatTranscriber):
    """STT por defecto: Whisper large-v3 en Groq (capa gratuita).

    Requiere GROQ_API_KEY en el entorno (nunca en el repo; ver .env).
    """

    env_var = "GROQ_API_KEY"
    base_url = "https://api.groq.com/openai/v1"
    default_model = "whisper-large-v3"


class WhisperTranscriber(_OpenAICompatTranscriber):
    """STT con Whisper via API de OpenAI. Requiere OPENAI_API_KEY."""

    env_var = "OPENAI_API_KEY"
    base_url = None
    default_model = "whisper-1"


def build_transcriber() -> Transcriber:
    """Elige el STT segun las claves disponibles: Groq (preferido) u OpenAI.

    No falla si faltan claves: devuelve el transcriptor preferido y este lanza
    un error claro recien al transcribir (lo captura VoicePipeline.process).
    """
    if os.getenv("GROQ_API_KEY"):
        return GroqTranscriber()
    if os.getenv("OPENAI_API_KEY"):
        return WhisperTranscriber()
    return GroqTranscriber()  # default; avisa al primer uso si falta la clave
