"""Arranque del bot de Telegram (Fase 2, texto).

Conecta los comandos /stock, /precio y /pedidos con la logica de handlers.py.
El import de python-telegram-bot esta protegido: los tests NO requieren la
libreria ni un TELEGRAM_BOT_TOKEN real. La logica vive en handlers.py.

Uso real:
    export TELEGRAM_BOT_TOKEN=...        # nunca se commitea
    export MEDUSA_BACKEND_URL=...
    export MEDUSA_PUBLISHABLE_KEY=...
    export MEDUSA_REGION_ID=...
    export MEDUSA_ADMIN_TOKEN=...        # para /pedidos
    python bot.py
"""
from __future__ import annotations

import os

import handlers
from medusa_client import MedusaClient


def build_client() -> MedusaClient:
    return MedusaClient()


def main() -> None:
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
    )

    client = build_client()

    async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = " ".join(context.args) if context.args else ""
        await update.message.reply_text(handlers.handle_stock(client, query))

    async def precio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = " ".join(context.args) if context.args else ""
        await update.message.reply_text(handlers.handle_precio(client, query))

    async def pedidos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(handlers.handle_pedidos(client))

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("stock", stock))
    app.add_handler(CommandHandler("precio", precio))
    app.add_handler(CommandHandler("pedidos", pedidos))
    app.run_polling()


if __name__ == "__main__":
    main()
