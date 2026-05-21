# Bot de Telegram (Fase 2-3). Imagen lean de produccion.
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencias primero (mejor cache de capas)
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Codigo del bot (los tests y el venv quedan fuera via .dockerignore)
COPY *.py ./

# Usuario sin privilegios
RUN useradd --create-home appuser
USER appuser

# Los secretos (TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, etc.) se inyectan por env
# en runtime; NUNCA se hornean en la imagen.
CMD ["python", "bot.py"]
