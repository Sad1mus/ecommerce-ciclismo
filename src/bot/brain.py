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
from history import HistoryStore, MemoryHistoryStore
from medusa_client import MedusaClient
from tools import TOOLS_SPEC, WRITE_TOOLS, execute_tool

logger = logging.getLogger("bot.brain")
# Rastro de operaciones que mutan el negocio (quien/que/resultado). Un negocio real
# necesita saber quien facturo o despacho: este logger deja esa auditoria.
audit = logging.getLogger("bot.audit")

MAX_TOOL_ROUNDS = 5
# Historial corto: cada mensaje se reenvia en cada llamada y consume tokens del
# cupo diario de Groq. 12 da contexto suficiente para una conversacion operativa.
MAX_HISTORY_MSGS = 12  # ademas del system prompt
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
# OpenRouter da acceso a muchos modelos; el default espeja al 70B (tool-calling fiable).
# DEBE soportar function-calling (el 8b de Groq NO sirve; ojo al elegir en OpenRouter).
DEFAULT_OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct"
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


class OpenAICompatLLM:
    """LLM real sobre cualquier API compatible con OpenAI (Groq, OpenRouter, ...).

    Groq y OpenRouter hablan el mismo protocolo; solo cambian base_url, la variable
    de la clave y el modelo. El import de `openai` es DIFERIDO (los tests no lo usan).
    """

    def __init__(self, *, name: str, api_key_env: str, base_url: str, model: str) -> None:
        self.name = name
        self.api_key_env = api_key_env
        self.base_url = base_url
        self.model = model

    def _api_key(self) -> str:
        key = os.getenv(self.api_key_env)
        if not key:
            raise RuntimeError(f"Falta {self.api_key_env} para el proveedor {self.name}.")
        return key

    def chat(self, messages: List[dict], tools: List[dict]) -> dict:  # pragma: no cover - red/clave
        from openai import OpenAI

        client = OpenAI(api_key=self._api_key(), base_url=self.base_url)
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
                # Errores no recuperables: no insistir (dejar que el fallback actue).
                if "AuthenticationError" in nombre or "BadRequestError" in nombre:
                    raise
                espera = 2 * (intento + 1)
                logger.warning("%s fallo (%s), reintento %d/%d en %ds", self.name, nombre, intento + 1, LLM_RETRIES, espera)
                time.sleep(espera)
        if resp is None:
            raise ultimo_error if ultimo_error else RuntimeError(f"{self.name} no respondio.")
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


class GroqLLM(OpenAICompatLLM):
    """Llama via API de Groq (compatible con OpenAI). Capa gratuita con cupo diario."""

    def __init__(self, model: str | None = None) -> None:
        super().__init__(
            name="groq",
            api_key_env="GROQ_API_KEY",
            base_url="https://api.groq.com/openai/v1",
            model=model or os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL),
        )


class OpenRouterLLM(OpenAICompatLLM):
    """Modelos via OpenRouter (compatible con OpenAI). Mejor opcion / fallback de Groq."""

    def __init__(self, model: str | None = None) -> None:
        super().__init__(
            name="openrouter",
            api_key_env="OPENROUTER_KEY",
            base_url="https://openrouter.ai/api/v1",
            model=model or os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL),
        )


class FallbackLLM:
    """Envuelve dos proveedores: si el primario falla (cae o agota cupo), usa el secundario.

    Anti-alucinacion: el fallback NO inventa; solo cambia de proveedor para la MISMA
    consulta con las MISMAS herramientas.
    """

    def __init__(self, primary: LLM, secondary: LLM) -> None:
        self.primary = primary
        self.secondary = secondary
        self.name = f"{getattr(primary, 'name', '?')}+{getattr(secondary, 'name', '?')}"

    def chat(self, messages: List[dict], tools: List[dict]) -> dict:
        try:
            return self.primary.chat(messages, tools)
        except Exception as e:  # noqa: BLE001 - primario caido/sin cupo: probar el secundario
            logger.warning(
                "Proveedor primario %s fallo (%s); uso el secundario %s",
                getattr(self.primary, "name", "?"), type(e).__name__, getattr(self.secondary, "name", "?"),
            )
            return self.secondary.chat(messages, tools)


def build_llm(env: dict | None = None) -> LLM:
    """Construye el cerebro segun el entorno.

    LLM_PROVIDER selecciona el primario (groq|openrouter; default groq). Si la clave
    del OTRO proveedor esta presente, se arma un FallbackLLM para tolerar caidas/cupo.
    """
    env = env if env is not None else os.environ
    provider = (env.get("LLM_PROVIDER") or "groq").strip().lower()
    builders = {"groq": GroqLLM, "openrouter": OpenRouterLLM}
    primary_cls = builders.get(provider, GroqLLM)
    primary = primary_cls()

    other = "openrouter" if primary.name != "openrouter" else "groq"
    other_key_env = "OPENROUTER_KEY" if other == "openrouter" else "GROQ_API_KEY"
    if env.get(other_key_env):
        return FallbackLLM(primary, builders[other]())
    return primary


class Brain:
    """Agente conversacional con memoria por chat. Orquesta tools; no inventa.

    - `store`: donde persiste el historial (Redis en prod, memoria en dev/test). Por
      defecto memoria, para no romper tests ni dev sin Redis.
    - `limiter`: rate-limit opcional por chat_id (protege el cupo del LLM ante spam).
    """

    def __init__(
        self,
        llm: LLM,
        client: MedusaClient,
        store: HistoryStore | None = None,
        limiter=None,
    ) -> None:
        self.llm = llm
        self.client = client
        self.store = store or MemoryHistoryStore()
        self.limiter = limiter

    def _load(self, chat_id: str) -> List[dict]:
        hist = self.store.load(chat_id)
        if not hist:
            return [{"role": "system", "content": SYSTEM_PROMPT}]
        return hist

    @staticmethod
    def _trim(hist: List[dict]) -> List[dict]:
        """Conserva el system prompt + los ultimos MAX_HISTORY_MSGS mensajes."""
        if len(hist) > MAX_HISTORY_MSGS + 1:
            return [hist[0]] + hist[-MAX_HISTORY_MSGS:]
        return hist

    def reset(self, chat_id: str) -> None:
        self.store.delete(chat_id)

    def handle(self, chat_id: str, texto: str) -> str:
        """Procesa un turno del dueño y devuelve la respuesta (texto accesible)."""
        texto = (texto or "").strip()
        if not texto:
            return "No entendi. ¿Me lo repites?"
        # Rate-limit ANTES de tocar el LLM: el spam no debe quemar el cupo diario.
        if self.limiter is not None and not self.limiter.allow(chat_id):
            return "Estas enviando muchos mensajes muy seguido. Dame un momento y reintenta, por favor."

        hist = self._load(chat_id)
        hist.append({"role": "user", "content": texto})

        for _ in range(MAX_TOOL_ROUNDS):
            try:
                msg = self.llm.chat(hist, TOOLS_SPEC)
            except Exception as e:
                # El cerebro no esta disponible: no inventamos, avisamos (y dejamos rastro).
                # No persistimos el turno a medias (queda el mensaje del usuario sin respuesta).
                logger.error("Fallo al consultar el LLM: %s: %s", type(e).__name__, e)
                if "RateLimit" in type(e).__name__:
                    return "Estoy con mucha demanda en este momento. Dame unos segundos y repite, por favor."
                return "Ahora mismo no puedo procesar tu mensaje. Intenta de nuevo en un momento."
            hist.append(msg)
            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                hist = self._trim(hist)
                self.store.save(chat_id, hist)
                return clamp_lines((msg.get("content") or "").strip() or "Listo.")
            for tc in tool_calls:
                fn = tc.get("function", {})
                name = fn.get("name", "")
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except (json.JSONDecodeError, TypeError):
                    args = {}
                resultado = execute_tool(name, args, self.client)
                if name in WRITE_TOOLS:
                    # Auditoria: quien (chat_id), que (tool + args) y el resultado resumido.
                    audit.info(
                        "chat_id=%s tool=%s args=%s -> %s",
                        chat_id, name, json.dumps(args, ensure_ascii=False), (resultado or "")[:120],
                    )
                hist.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": resultado})

        hist = self._trim(hist)
        self.store.save(chat_id, hist)
        return "No pude completar la accion despues de varios intentos. ¿La reformulamos?"
