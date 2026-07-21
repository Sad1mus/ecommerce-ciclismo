"""Arranque del bot de Telegram — la "mano derecha" del dueño no vidente.

El dueño habla NATURAL (texto o voz) y el cerebro conversacional (brain.py, LLM
con tool-calling sobre Groq) entiende e invoca herramientas que leen/operan Medusa.
Los comandos /stock, /precio, etc. quedan como ATAJOS opcionales.

El import de python-telegram-bot esta protegido: los tests NO requieren la
libreria ni claves reales.

Uso real:
    export TELEGRAM_BOT_TOKEN=...        # nunca se commitea
    export GROQ_API_KEY=...              # cerebro (LLM) + voz (Whisper)
    export MEDUSA_BACKEND_URL=... MEDUSA_PUBLISHABLE_KEY=... MEDUSA_REGION_ID=...
    export MEDUSA_ADMIN_EMAIL=... MEDUSA_ADMIN_PASSWORD=...   # pedidos/operacion
    python bot.py
"""
from __future__ import annotations

import logging
import os

import handlers
from agents import LogisticaAgent, ReportesAgent, VentasAgent
from auth import DENEGADO, is_allowed, load_allowlist, log_startup_state
from brain import Brain, GroqLLM
from medusa_client import MedusaClient
from voice import build_transcriber


def build_client() -> MedusaClient:
    return MedusaClient()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # Silencia el ruido del polling (y evita registrar el token en cada getUpdates).
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram.ext.Updater").setLevel(logging.WARNING)
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit(
            "Falta TELEGRAM_BOT_TOKEN. Exporta la variable (no se guarda en el repo)."
        )

    # Import diferido: solo necesario para la ejecucion real.
    from telegram import Update
    from telegram.ext import (
        Application,
        CommandHandler,
        ContextTypes,
        MessageHandler,
        filters,
    )

    client = build_client()
    ventas = VentasAgent(client)
    logistica = LogisticaAgent(client)
    reportes = ReportesAgent(client)
    transcriber = build_transcriber()      # oidos: Whisper via Groq
    brain = Brain(GroqLLM(), client)       # cerebro: LLM con herramientas

    # Control de acceso: el bot OPERA el negocio, no debe responder a cualquiera.
    allowlist = load_allowlist()
    log_startup_state(allowlist)           # WARNING bien visible si queda abierto

    def _chat_id(update) -> str:
        return str(update.effective_chat.id)

    def restringido(handler):
        """Envuelve un handler: solo lo ejecuta para chat_id autorizados.

        Si la allowlist esta vacia (dev/demo) deja pasar a todos (is_allowed).
        A un chat_id no autorizado le responde con una negativa y loguea el intento.
        """
        async def wrapper(update, context):
            chat_id = _chat_id(update)
            if not is_allowed(chat_id, allowlist):
                logging.getLogger("bot.auth").warning(
                    "Acceso DENEGADO a chat_id %s (no esta en la allowlist)", chat_id
                )
                await update.message.reply_text(DENEGADO)
                return
            return await handler(update, context)

        return wrapper

    async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = " ".join(context.args) if context.args else ""
        await update.message.reply_text(handlers.handle_stock(client, query))

    async def precio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = " ".join(context.args) if context.args else ""
        await update.message.reply_text(handlers.handle_precio(client, query))

    async def pedidos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(handlers.handle_pedidos(client))

    async def cmd_ventas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = " ".join(context.args) if context.args else ""
        await update.message.reply_text(ventas.consultar(query))

    async def cmd_logistica(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(logistica.estado_pedidos())

    async def cmd_reportes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = " ".join(context.args) if context.args else ""
        await update.message.reply_text(reportes.resumen(query))

    async def reiniciar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        brain.reset(_chat_id(update))
        await update.message.reply_text("Listo, empecemos de nuevo. ¿En que te ayudo?")

    async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # Texto natural -> cerebro conversacional (entiende e invoca herramientas).
        respuesta = brain.handle(_chat_id(update), update.message.text or "")
        await update.message.reply_text(respuesta)

    async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # Nota de voz -> transcripcion (Whisper/Groq) -> cerebro conversacional.
        archivo = await context.bot.get_file(update.message.voice.file_id)
        audio = bytes(await archivo.download_as_bytearray())
        try:
            texto = transcriber.transcribe(audio)
        except Exception:
            await update.message.reply_text(
                "No pude entender el audio. ¿Me lo repites, por favor?"
            )
            return
        await update.message.reply_text(brain.handle(_chat_id(update), texto))

    app = Application.builder().token(token).build()
    # Atajos por comando (opcionales). Todos pasan por la guarda de acceso.
    app.add_handler(CommandHandler("stock", restringido(stock)))
    app.add_handler(CommandHandler("precio", restringido(precio)))
    app.add_handler(CommandHandler("pedidos", restringido(pedidos)))
    app.add_handler(CommandHandler("ventas", restringido(cmd_ventas)))
    app.add_handler(CommandHandler("logistica", restringido(cmd_logistica)))
    app.add_handler(CommandHandler("reportes", restringido(cmd_reportes)))
    app.add_handler(CommandHandler("reiniciar", restringido(reiniciar)))
    # Conversacion natural: voz y texto (texto que NO sea un comando).
    app.add_handler(MessageHandler(filters.VOICE, restringido(on_voice)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, restringido(on_text)))
    app.run_polling()


if __name__ == "__main__":
    main()
