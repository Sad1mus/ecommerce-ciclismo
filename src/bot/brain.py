"""Cerebro conversacional del bot — la "mano derecha" del dueño no vidente.

El dueño habla NATURAL (texto o voz); este modulo usa un LLM con tool-calling para
entender la intencion y llamar a las herramientas (tools.py), que son la unica
fuente de datos. El LLM NUNCA inventa cifras: solo orquesta y redacta natural.

Diseño testeable: el acceso al LLM esta detras del protocolo `LLM`; en los tests
se inyecta un LLM falso y NO se necesita GROQ_API_KEY ni red. En produccion se usa
`GroqLLM` (Llama via API de Groq, compatible con OpenAI).

ANTI-ALUCINACION + ACCESIBILIDAD + CONFIRMACION viven en SYSTEM_PROMPT y, ademas,
estan reforzadas en codigo: las tools de escritura no mutan sin `confirmado=True`.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import List, Protocol

from formatting import clamp_lines
from medusa_client import MedusaClient
from tools import TOOLS_SPEC, execute_tool

logger = logging.getLogger("bot.brain")

MAX_TOOL_ROUNDS = 5
# Historial corto: cada mensaje se reenvia en cada llamada y consume tokens del
# cupo diario de Groq. 12 da contexto suficiente para una conversacion operativa.
MAX_HISTORY_MSGS = 12  # ademas del system prompt
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
LLM_RETRIES = 3  # reintentos ante errores transitorios (rate limit, red)

SYSTEM_PROMPT = (
    "Eres el asistente de confianza ('mano derecha') del dueño de una tienda de "
    "ciclismo en Colombia. El dueño es NO VIDENTE y te habla por voz o texto; tus "
    "respuestas se leen con lector de pantalla.\n\n"
    "REGLAS INQUEBRANTABLES:\n"
    "1. NUNCA inventes datos. Stock, precios, pedidos y totales SIEMPRE salen de las "
    "herramientas. Si no llamaste a una herramienta, no afirmes cifras. Si una "
    "herramienta dice que no hay dato, dilo con honestidad.\n"
    "2. Para CUALQUIER accion que cambie algo (crear o confirmar un pedido, facturar, "
    "preparar empaque, marcar transportadora) PRIMERO describe lo que vas a hacer y "
    "PIDE confirmacion. Solo ejecuta con confirmado=true DESPUES de que el dueño diga "
    "si claramente. Nunca asumas el si.\n"
    "3. Accesibilidad: responde en español de Colombia, en texto plano, SIN emojis, "
    "SIN tablas ni simbolos de alineacion. Frases cortas, una idea por linea. Montos "
    "en pesos colombianos.\n"
    "4. Se breve y directo, como un buen asistente al telefono. Si falta un dato para "
    "actuar (p.ej. el numero de pedido o la transportadora), preguntalo.\n"
    "5. El dueño piensa en SUS propias categorias/codigos (como 1-RK, 6-CL, PITILLOS). "
    "Si menciona uno, usa buscar_por_codigo_interno. La tienda al publico usa categorias "
    "por tipo (Cascos, Candados...); para esas usa productos_por_categoria o "
    "listar_categorias. No mezcles ni inventes categorias.\n"
)


class LLM(Protocol):
    def chat(self, messages: List[dict], tools: List[dict]) -> dict:  # pragma: no cover
        """Devuelve un mensaje 'assistant' en formato OpenAI (dict)."""
        ...


class GroqLLM:
    """LLM real: Llama via API de Groq (compatible con OpenAI). Import diferido."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)

    def chat(self, messages: List[dict], tools: List[dict]) -> dict:  # pragma: no cover - red/clave
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("Falta GROQ_API_KEY para el cerebro del bot.")
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        # Reintento ante errores transitorios (rate limit del free tier, red, 5xx).
        ultimo_error: Exception | None = None
        resp = None
        for intento in range(LLM_RETRIES):
            try:
                resp = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0,
                )
                break
            except Exception as e:  # noqa: BLE001 - reintentamos cualquier fallo de API
                ultimo_error = e
                nombre = type(e).__name__
                # Errores no recuperables: no insistir.
                if "AuthenticationError" in nombre or "BadRequestError" in nombre:
                    raise
                espera = 2 * (intento + 1)
                logger.warning("Groq fallo (%s), reintento %d/%d en %ds", nombre, intento + 1, LLM_RETRIES, espera)
                time.sleep(espera)
        if resp is None:
            raise ultimo_error if ultimo_error else RuntimeError("Groq no respondio.")
        m = resp.choices[0].message
        out: dict = {"role": "assistant", "content": m.content or ""}
        if getattr(m, "tool_calls", None):
            out["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in m.tool_calls
            ]
            out["content"] = m.content or ""  # OpenAI exige content (puede ser "")
        return out


class Brain:
    """Agente conversacional con memoria por chat. Orquesta tools; no inventa."""

    def __init__(self, llm: LLM, client: MedusaClient) -> None:
        self.llm = llm
        self.client = client
        self._histories: dict[str, List[dict]] = {}

    def _history(self, chat_id: str) -> List[dict]:
        if chat_id not in self._histories:
            self._histories[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
        return self._histories[chat_id]

    def _trim(self, chat_id: str) -> None:
        """Conserva el system prompt + los ultimos MAX_HISTORY_MSGS mensajes."""
        hist = self._histories[chat_id]
        if len(hist) > MAX_HISTORY_MSGS + 1:
            self._histories[chat_id] = [hist[0]] + hist[-MAX_HISTORY_MSGS:]

    def reset(self, chat_id: str) -> None:
        self._histories.pop(chat_id, None)

    def handle(self, chat_id: str, texto: str) -> str:
        """Procesa un turno del dueño y devuelve la respuesta (texto accesible)."""
        texto = (texto or "").strip()
        if not texto:
            return "No entendi. ¿Me lo repites?"
        hist = self._history(chat_id)
        hist.append({"role": "user", "content": texto})

        for _ in range(MAX_TOOL_ROUNDS):
            try:
                msg = self.llm.chat(hist, TOOLS_SPEC)
            except Exception as e:
                # El cerebro no esta disponible: no inventamos, avisamos (y dejamos rastro).
                logger.error("Fallo al consultar el LLM: %s: %s", type(e).__name__, e)
                if "RateLimit" in type(e).__name__:
                    return "Estoy con mucha demanda en este momento. Dame unos segundos y repite, por favor."
                return "Ahora mismo no puedo procesar tu mensaje. Intenta de nuevo en un momento."
            hist.append(msg)
            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                self._trim(chat_id)
                return clamp_lines((msg.get("content") or "").strip() or "Listo.")
            for tc in tool_calls:
                fn = tc.get("function", {})
                name = fn.get("name", "")
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except (json.JSONDecodeError, TypeError):
                    args = {}
                resultado = execute_tool(name, args, self.client)
                hist.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": resultado})

        self._trim(chat_id)
        return "No pude completar la accion despues de varios intentos. ¿La reformulamos?"
