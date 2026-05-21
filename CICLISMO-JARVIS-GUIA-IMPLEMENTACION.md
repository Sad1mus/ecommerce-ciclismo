# Ecommerce Ciclismo — Guia de Implementacion con JARVIS v2

> Adaptacion del proyecto Ecommerce Ciclismo v3.0 al stack JARVIS v2
> Respetando la arquitectura JARVIS: OpenCode Go + LiteLLM + OpenRouter + n8n + Obsidian + VS Code
> Fecha: Mayo 2026

---

## Tabla de Contenidos

1. [Resumen de Adaptacion](#1-resumen-de-adaptacion)
2. [Mapeo de Modelos: Documento Original vs JARVIS](#2-mapeo-de-modelos)
3. [Estructura del Proyecto en JARVIS](#3-estructura-del-proyecto)
4. [LiteLLM Config — Routing Especifico Ciclismo](#4-litellm-config)
5. [Skills del Proyecto — 9 Agentes Ciclismo](#5-skills-del-proyecto)
6. [Docker Compose — Produccion Ciclismo](#6-docker-compose-produccion)
7. [Obsidian Vault — Proyecto Ciclismo](#7-obsidian-vault)
8. [OpenCode Config — Proyecto Ciclismo](#8-opencode-config)
9. [Plan de Ejecucion Semana a Semana](#9-plan-de-ejecucion)
10. [Comandos de Inicio](#10-comandos-de-inicio)

---

## 1. Resumen de Adaptacion

### Que cambia y que se mantiene

| Componente | Documento v3 original | Adaptacion JARVIS v2 | Cambia? |
|-----------|----------------------|---------------------|---------|
| Coding agent | Claude Code + Antigravity | **OpenCode Go** + Obsidian | SI |
| Gateway modelos | OpenRouter directo | **LiteLLM** -> OpenRouter | SI |
| Modelo complejo | Claude Sonnet 4.5 via OpenRouter | **coder** (Qwen3 Coder 30B / Sonnet) via LiteLLM | SI |
| Modelo simple | Claude Haiku 4.5 via OpenRouter | **fast** (Qwen2.5 Coder 7B local / Haiku) via LiteLLM | SI |
| Modelo reportes | DeepSeek Chat v3 via OpenRouter | **thinker** (DeepSeek R1) via LiteLLM | SI |
| Modelo premium | Claude Opus 4.6 | **premium** (Claude Sonnet 4) via LiteLLM | SI |
| STT Voz | Whisper via OpenAI API | **Igual** — Whisper via OpenAI API | NO |
| Memoria persistente | Antigravity | **Obsidian Vault** + Qdrant | SI |
| IDE | VS Code | **Igual** — VS Code + OpenCode | NO |
| Backend ecommerce | MedusaJS v2 | **Igual** | NO |
| Base de datos | PostgreSQL 15 | **Igual** | NO |
| Cache | Redis 7 | **Igual** | NO |
| Automatizacion | n8n self-hosted | **Igual** | NO |
| Bot Telegram | python-telegram-bot 20.7 | **Igual** | NO |
| Storefront | Next.js 14 | **Igual** | NO |
| Pagos Colombia | Wompi + ePayco | **Igual** | NO |
| Seguridad | OWASP + audit log | **Igual** | NO |
| Infra | Docker Compose + VPS | **Igual** + Monitor Agent JARVIS | NO |
| Backups | Backblaze B2 | **Igual** | NO |

### Principio rector

**Todo lo que no sea el stack de modelos se mantiene exactamente igual.** La unica adaptacion es COMO los agentes acceden a los modelos: en vez de llamadas directas a OpenRouter o Anthropic, todo pasa por LiteLLM local, que enruta al modelo mas barato segun la tarea, con failover automatico y tracking de costos.

---

## 2. Mapeo de Modelos

### 2.1 Tabla de equivalencia

| Agente Ciclismo | Modelo en doc original | Modelo JARVIS via LiteLLM | Config en LiteLLM |
|----------------|----------------------|--------------------------|-------------------|
| Orquestador | Claude Sonnet 4.5 | `coder` (Qwen3 Coder 30B, failover a Sonnet) | Prioridad: Ollama local -> OpenRouter |
| Inventario | Claude Haiku 4.5 | `fast` (Qwen2.5 Coder 7B local, failover a Haiku) | Prioridad: Ollama local -> OpenRouter |
| Ventas | Claude Sonnet 4.5 | `coder` (Qwen3 Coder 30B, failover a Sonnet) | Prioridad: Ollama local -> OpenRouter |
| Logistica | Claude Haiku 4.5 | `fast` (Qwen2.5 Coder 7B local, failover a Haiku) | Prioridad: Ollama local -> OpenRouter |
| Ecommerce | Claude Sonnet 4.5 | `coder` (Qwen3 Coder 30B, failover a Sonnet) | Prioridad: Ollama local -> OpenRouter |
| Reportes | DeepSeek Chat v3 | `thinker` (DeepSeek R1) | OpenRouter directo |
| Seguridad | Claude Haiku 4.5 | `fast` (Qwen2.5 Coder 7B local, failover a Haiku) | Prioridad: Ollama local -> OpenRouter |
| Backup | Script bash | N/A (no usa LLM) | N/A |
| PM/Dev | Claude Sonnet 4.5 | `coder` o `premium` (manual) | Tu decides en cada sesion |

### 2.2 Estrategia de costo

```
DOC ORIGINAL (directo a OpenRouter):
  Orquestador: Sonnet 4.5 x ~500 msgs/dia = ~$25/mes
  Inventario:  Haiku 4.5    x ~300 msgs/dia = ~$5/mes
  Ventas:      Sonnet 4.5   x ~200 msgs/dia = ~$10/mes
  Logistica:   Haiku 4.5    x ~150 msgs/dia = ~$3/mes
  Ecommerce:   Sonnet 4.5   x ~50 msgs/dia  = ~$3/mes
  Reportes:    DeepSeek     x ~20 msgs/dia   = ~$1/mes
  Seguridad:   Haiku 4.5    x ~100 msgs/dia  = ~$2/mes
  TOTAL: ~$49/mes solo en modelos de produccion

JARVIS v2 (via LiteLLM con Ollama first):
  Orquestador: Ollama local (gratis) + Sonnet solo cuando falla = ~$5/mes
  Inventario:  Ollama local (gratis) + Haiku solo cuando falla  = ~$1/mes
  Ventas:      Ollama local (gratis) + Sonnet solo cuando falla = ~$3/mes
  Logistica:   Ollama local (gratis) + Haiku solo cuando falla  = ~$1/mes
  Ecommerce:   Ollama local (gratis) + Sonnet solo cuando falla = ~$1/mes
  Reportes:    DeepSeek R1 via OpenRouter                       = ~$1/mes
  Seguridad:   Ollama local (gratis) + Haiku solo cuando falla  = ~$1/mes
  TOTAL: ~$13/mes en modelos de produccion

AHORRO: ~$36/mes (73% menos)
```

**Como funciona**: Ollama corre en tu Xubuntu LOCAL para desarrollo. En produccion (VPS sin GPU), LiteLLM enruta directo a OpenRouter. El ahorro real viene en la fase de desarrollo donde el 80% de las llamadas van a Ollama local.

---

## 3. Estructura del Proyecto en JARVIS

```
~/jarvis/projects/ecommerce-ciclismo/
|
+-- .opencode/
|   +-- skills/                       # Skills especificos del proyecto
|   |   +-- orquestador/
|   |   |   +-- SKILL.md
|   |   |   +-- metadata.json
|   |   +-- inventario/
|   |   |   +-- SKILL.md
|   |   |   +-- scripts/
|   |   |   |   +-- check_stock.sh
|   |   |   |   +-- alert_stock.sh
|   |   |   +-- metadata.json
|   |   +-- ventas/
|   |   |   +-- SKILL.md
|   |   |   +-- scripts/
|   |   |   |   +-- create_factura.sh
|   |   |   |   +-- cotizar.sh
|   |   |   +-- metadata.json
|   |   +-- logistica/
|   |   |   +-- SKILL.md
|   |   |   +-- scripts/
|   |   |   |   +-- despacho.sh
|   |   |   |   +-- picking_list.sh
|   |   |   +-- metadata.json
|   |   +-- ecommerce/
|   |   |   +-- SKILL.md
|   |   |   +-- metadata.json
|   |   +-- reportes/
|   |   |   +-- SKILL.md
|   |   |   +-- scripts/
|   |   |   |   +-- weekly_report.sh
|   |   |   +-- metadata.json
|   |   +-- seguridad/
|   |   |   +-- SKILL.md
|   |   |   +-- metadata.json
|   |   +-- accesibilidad/            # Skill unico: admin no vidente
|   |   |   +-- SKILL.md
|   |   |   +-- metadata.json
|   |   +-- colombia-payments/        # Skill unico: pagos colombianos
|   |   |   +-- SKILL.md
|   |   |   +-- metadata.json
|   |   +-- anti-hallucination/       # Skill unico: fuente unica de verdad
|   |       +-- SKILL.md
|   |       +-- metadata.json
|   |
|   +-- rules/                        # Reglas del proyecto
|       +-- no-llm-for-data.md        # JAMAS usar LLM para stock/precios
|       +-- text-only-output.md        # Sin emojis, sin tablas, max 10 lineas
|       +-- confirm-before-write.md    # Confirmacion 2 pasos en acciones irreversibles
|       +-- accessibility-tts.md       # Reglas admin no vidente
|
+-- src/
|   +-- medusa/                       # MedusaJS v2 backend
|   |   +-- medusa-config.js
|   |   +-- package.json
|   |   +-- src/
|   |       +-- api/
|   |       +-- models/
|   |       +-- services/
|   |       +-- subscribers/
|   |
|   +-- bot/                          # Bot Telegram + Whisper
|   |   +-- main.py
|   |   +-- handlers/
|   |   |   +-- voice.py              # Handler de voz con Whisper
|   |   |   +-- commands.py           # Todos los comandos del bot
|   |   |   +-- text_handler.py       # Texto libre + orquestacion
|   |   +-- agents/                   # Logica de cada agente
|   |   |   +-- orquestador.py
|   |   |   +-- inventario.py
|   |   |   +-- ventas.py
|   |   |   +-- logistica.py
|   |   |   +-- reportes.py
|   |   |   +-- seguridad.py
|   |   +-- services/
|   |   |   +-- medusa_client.py      # Cliente API MedusaJS
|   |   |   +-- litellm_client.py     # Cliente LiteLLM para agentes
|   |   |   +-- whisper_client.py     # Cliente Whisper STT
|   |   |   +-- audit_log.py          # Audit log inmutable
|   |   +-- requirements.txt
|   |
|   +-- storefront/                   # Next.js 14 storefront
|       +-- package.json
|       +-- src/
|           +-- app/
|           +-- components/
|           +-- lib/
|
+-- docker-compose.yml                # Stack completo del proyecto
+-- docker-compose.prod.yml           # Produccion con monitor
+-- .env.example
+-- .gitignore
+-- Dockerfile.bot
+-- Dockerfile.medusa
+-- Dockerfile.storefront
+-- nginx.conf
+-- backup_diario.sh
+-- CLAUDE.md                         # Reemplazado por SKILL.md + Obsidian
```

---

## 4. LiteLLM Config — Routing Especifico Ciclismo

Archivo: `~/jarvis/projects/ecommerce-ciclismo/litellm-config.yaml`

```yaml
model_list:
  # ================================================================
  # CODER — Para: Orquestador, Ventas, Ecommerce, PM/Dev
  # Tareas complejas: facturacion, logica de negocio, sincronizacion
  # ================================================================
  - model_name: coder
    litellm_params:
      model: ollama_chat/qwen2.5-coder:7b
      api_base: http://ollama:11434
    model_info:
      mode: chat
      cost: free

  - model_name: coder
    litellm_params:
      model: openrouter/qwen/qwen3-coder-30b
      api_key: os.environ/OPENROUTER_KEY
    model_info:
      mode: chat
      cost: low

  - model_name: coder
    litellm_params:
      model: openrouter/anthropic/claude-sonnet-4-20250514
      api_key: os.environ/OPENROUTER_KEY
    model_info:
      mode: chat
      cost: medium

  # ================================================================
  # FAST — Para: Inventario, Logistica, Seguridad
  # Tareas simples: consultar stock, verificar estado, rate limiting
  # ALTA FRECUENCIA: estos agentes se llaman decenas de veces al dia
  # ================================================================
  - model_name: fast
    litellm_params:
      model: ollama_chat/qwen2.5-coder:7b
      api_base: http://ollama:11434
    model_info:
      mode: chat
      cost: free

  - model_name: fast
    litellm_params:
      model: openrouter/anthropic/claude-haiku-4-20250514
      api_key: os.environ/OPENROUTER_KEY
    model_info:
      mode: chat
      cost: low

  # ================================================================
  # THINKER — Para: Reportes
  # Analisis profundo, resumenes, comisiones, tendencias
  # ================================================================
  - model_name: thinker
    litellm_params:
      model: openrouter/deepseek/deepseek-r1
      api_key: os.environ/OPENROUTER_KEY
    model_info:
      mode: chat
      cost: low

  # ================================================================
  # PREMIUM — Solo para: decisiones arquitectonicas criticas
  # No se usa en produccion, solo en desarrollo manual
  # ================================================================
  - model_name: premium
    litellm_params:
      model: anthropic/claude-sonnet-4-20250514
      api_key: os.environ/ANTHROPIC_KEY
    model_info:
      mode: chat
      cost: high

  # ================================================================
  # WHISPER — Para: Transcripcion de voz
  # OpenAI Whisper API, pasa directo (no por LiteLLM como LLM)
  # Se llama directamente desde el bot: openai.Audio.transcribe()
  # ================================================================

# ================================================================
# ROUTER SETTINGS
# ================================================================
router_settings:
  num_retries: 2
  timeout: 120
  fallbacks:
    - {"coder": ["fast"]}       # Si coder falla, usar fast
    - {"fast": ["coder"]}       # Si fast falla, usar coder
    - {"thinker": ["coder"]}    # Si thinker falla, usar coder

# ================================================================
# MAPEO DE AGENTES A MODELOS
# ================================================================
# Orquestador -> coder  (decisiones complejas de ruteo)
# Inventario  -> fast   (consultas simples de stock)
# Ventas      -> coder  (logica de descuentos y facturacion)
# Logistica   -> fast   (despachos, guias, seguimiento)
# Ecommerce   -> coder  (sincronizacion catalogo, pagos)
# Reportes    -> thinker (analisis, sintesis, comisiones)
# Seguridad   -> fast   (verificacion, audit, rate limit)
# Admin (tu)  -> premium (solo desarrollo manual)
```

### Cliente Python para el Bot

Archivo: `~/jarvis/projects/ecommerce-ciclismo/src/bot/services/litellm_client.py`

```python
"""
Cliente LiteLLM para agentes del bot Ciclismo.
Todos los agentes usan este cliente para llamar modelos.
LiteLLM enruta al modelo mas barato disponible.
"""
import httpx
import os

LITELLM_URL = os.getenv("LITELLM_URL", "http://localhost:4000")
LITELLM_KEY = os.getenv("LITELLM_KEY", "sk-jarvis-local")

# Mapeo de agente -> modelo LiteLLM
AGENT_MODEL_MAP = {
    "orquestador": "coder",
    "inventario":  "fast",
    "ventas":      "coder",
    "logistica":   "fast",
    "ecommerce":   "coder",
    "reportes":    "thinker",
    "seguridad":   "fast",
}


async def ask_agent(agent_name: str, system_prompt: str, user_message: str) -> str:
    """
    Llama al modelo asignado al agente via LiteLLM.
    LiteLLM decide si usa Ollama local o OpenRouter segun disponibilidad.
    """
    model = AGENT_MODEL_MAP.get(agent_name, "fast")

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{LITELLM_URL}/chat/completions",
            headers={"Authorization": f"Bearer {LITELLM_KEY}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.1,  # Baja temperatura: respuestas deterministas
                "max_tokens": 500,   # Max 10 lineas de respuesta
            }
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


async def transcribe_voice(audio_file_path: str) -> str:
    """
    Transcripcion de voz via OpenAI Whisper API.
    Este NO pasa por LiteLLM — es API directa de OpenAI.
    """
    import openai
    openai_client = openai.AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

    with open(audio_file_path, "rb") as audio:
        transcript = await openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio,
            language="es"
        )
    return transcript.text
```

---

## 5. Skills del Proyecto — 9 Agentes Ciclismo

### 5.1 Skill: Orquestador

Archivo: `~/jarvis/projects/ecommerce-ciclismo/.opencode/skills/orquestador/SKILL.md`

```markdown
# Orquestador — CEO/CTO del Sistema Ciclismo

Eres el agente orquestador del ecommerce de ciclismo. Recibes cada mensaje del administrador y decides a que agente especializado enrutarlo.

## Modelo asignado: coder (via LiteLLM)

## Responsabilidades
1. Recibir cada mensaje de texto o voz transcrito
2. Detectar la intencion del administrador
3. Enrutar al agente correcto
4. Consolidar la respuesta para el admin

## Tabla de ruteo
| Intencion detectada | Agente | Comandos |
|--------------------|--------|----------|
| Stock, disponibilidad, alertas | inventario | /stock, /carpeta, /alertas |
| Factura, cotizar, descuentos, clientes | ventas | /factura, /cotizar, /cliente |
| Despacho, guias, pedidos | logistica | /despacho, /pedido |
| Catalogo web, pagos, precios | ecommerce | /precio-admin |
| Reportes, ventas, comisiones | reportes | /reporte |
| Backup, seguridad | seguridad | /backup |

## Reglas ABSOLUTAS (del doc v3)
1. NUNCA responder con datos inventados. SIEMPRE query a la API primero.
2. Texto puro: sin emojis, sin tablas ASCII, sin caracteres especiales.
3. Precios en pesos COP verbalizados: 'cuarenta mil pesos' NO '$40.000'.
4. Respuestas maximo 10 lineas. Verbalizable por TTS en < 15 segundos.
5. Confirmar SI/NO antes de ejecutar acciones irreversibles.
6. Registrar TODA accion en tabla bot_audit_log inmutablemente.
7. Si el dato no esta en la API, decirlo honestamente. Nunca estimar.

## Stack tecnico del proyecto
- Backend: MedusaJS v2 (Node.js 20)
- DB: PostgreSQL 15
- Cache: Redis 7
- Bot: python-telegram-bot 20.7
- STT: OpenAI Whisper API (whisper-1, language='es')
- IA: LiteLLM -> Ollama local + OpenRouter
- Pagos: Wompi (Nequi, PSE, Bancolombia) + ePayco (Efecty)
- Infra: Docker Compose

## Carpertas del inventario
1-RK, 1.1-KL, 2-SPK, 3-RR, 4-BK, 5-MT, 6-CL

## Modelo de descuentos
Campo: customer.metadata.descuento_pct (float, 0-100)
Calculo: precio_final = precio_base * (1 - descuento_pct / 100)
Redondeo: entero mas cercano, sin decimales
```

Archivo: `~/jarvis/projects/ecommerce-ciclismo/.opencode/skills/orquestador/metadata.json`

```json
{
  "name": "orquestador-ciclismo",
  "version": "1.0.0",
  "description": "Agente orquestador del ecommerce ciclismo",
  "triggers": ["mensaje-entrante", "voz-transcrita"],
  "dependencies": ["litellm", "medusajs-api", "telegram-bot"],
  "model": "coder"
}
```

### 5.2 Skill: Inventario

Archivo: `~/jarvis/projects/ecommerce-ciclismo/.opencode/skills/inventario/SKILL.md`

```markdown
# Inventario — Jefe de Bodega Digital

Eres el agente de inventario. Gestionas stock en tiempo real, alertas de minimo y movimientos de bodega.

## Modelo asignado: fast (via LiteLLM)

## Regla ANTI-ALUCINACION (CRITICA)
- Stock: SIEMPRE consultar MedusaJS API /admin/products
- Precios: SIEMPRE consultar MedusaJS API variant.prices
- NUNCA usar la memoria del modelo para datos de stock o precios
- Si la API no responde, decir "No puedo consultar el inventario ahora"

## Comandos que manejas
- /stock [nombre] — Busca producto, muestra stock exacto y precio
- /carpeta [n] — Lista productos de la carpeta con stock actual
- /alertas — Productos con 5 unidades o menos

## Formato de respuesta (admin NO VIDENTE)
INCORRECTO: "Guante MTB | Stock: 47 | Precio: $29.325"
CORRECTO: "Guante mtb corto Azul: cuarenta y siete unidades disponibles. Precio base: veintinueve mil trescientos veinticinco pesos."

## API endpoints MedusaJS
- GET /admin/products?search={query} — Buscar producto
- GET /admin/products/{id} — Detalle con variantes y stock
- GET /admin/inventory-items — Stock por ubicacion

## Scripts disponibles
- `check_stock.sh <producto>` — Consulta stock via API
- `alert_stock.sh` — Lista productos con stock critico
```

### 5.3 Skill: Ventas

Archivo: `~/jarvis/projects/ecommerce-ciclismo/.opencode/skills/ventas/SKILL.md`

```markdown
# Ventas — Asesor Comercial

Eres el agente de ventas. Manejas pedidos mayorista y minorista, descuentos, cotizaciones y facturas.

## Modelo asignado: coder (via LiteLLM)

## Regla ANTI-ALUCINACION (CRITICA)
- Descuento del cliente: SIEMPRE consultar customer.metadata.descuento_pct en PostgreSQL
- NUNCA recordar descuentos del chat anterior
- NUNCA estimar precios

## Comandos que manejas
- /factura [cliente] [prod1 cant1]... — Crea orden con confirmacion previa
- /cotizar [cliente] [producto] — Precio con descuento sin crear factura
- /cliente [nombre] [%] — Asigna o actualiza descuento mayorista
- /precio-admin [SKU] [valor] — Actualiza precio (solo admin)

## Flujo de /factura (5 pasos obligatorios)
1. Validar stock de cada producto via MedusaJS API
2. Mostrar resumen con descuento aplicado, pedir confirmacion SI/NO
3. Si SI: crear Order en Medusa, reservar stock atomicamente en Redis
4. Notificar al canal de bodega (lista de picking)
5. Notificar al cliente via Telegram/WhatsApp
6. Registrar en bot_audit_log

## Confirmacion en 2 pasos (OBLIGATORIO)
Admin: /factura Carlos guante-azul 10 candado 5
Bot: CONFIRMAR FACTURA
  Cliente: Carlos Gomez (descuento 15%)
  Guante mtb corto Azul x10 — stock disponible: 34 unidades. OK.
  Candado espiral x5 — stock disponible: 18 unidades. OK.
  Total con descuento: trescientos un mil novecientos cuarenta y cuatro pesos.
  Responda SI para crear la factura o NO para cancelar.

## Formato de respuesta (admin NO VIDENTE)
Precios SIEMPRE verbalizados: 'ciento veinte mil pesos' NUNCA '$120.000'
```

### 5.4 Skill: Logistica

Archivo: `~/jarvis/projects/ecommerce-ciclismo/.opencode/skills/logistica/SKILL.md`

```markdown
# Logistica — Coordinador de Despachos

Eres el agente de logistica. Coordinas picking de bodega, guias de envio, transportadoras y seguimiento.

## Modelo asignado: fast (via LiteLLM)

## Comandos que manejas
- /despacho [factura] [transportadora] [guia] — Registra despacho
- /pedido [numero] — Estado completo del pedido

## Transportadoras Colombia
- Servientrega
- Coordinadora
- Interrapidisimo
- Envía (solo ciudades principales)

## Flujo de /despacho
1. Verificar que la orden existe en MedusaJS
2. Registrar guia y transportadora
3. Marcar fulfillment en Medusa
4. Notificar al cliente con numero de guia
5. Registrar en bot_audit_log

## Flujo de /pedido
1. Consultar MedusaJS /admin/orders/{id}
2. Mostrar: estado pago, estado envio, guia, total
3. Todo verbalizado, sin tablas
```

### 5.5 Skill: Anti-Hallucination

Archivo: `~/jarvis/projects/ecommerce-ciclismo/.opencode/skills/anti-hallucination/SKILL.md`

```markdown
# Anti-Hallucination — Fuente Unica de Verdad

Este skill define las reglas que PREVIENEN que los agentes inventen datos.
Es la proteccion mas critica del sistema porque el admin es NO VIDENTE.

## Principio fundamental
JAMAS usar el LLM como fuente de datos. El LLM es solo un procesador de lenguaje.
Los datos SIEMPRE vienen de APIs o bases de datos.

## Tabla de fuentes
| Tipo de dato | Fuente CORRECTA | Fuente PROHIBIDA |
|-------------|----------------|-----------------|
| Stock | MedusaJS API /admin/products | LLM / memoria del modelo |
| Precio | MedusaJS API variant.prices | Estimacion o calculo del modelo |
| Descuento | PostgreSQL customer.metadata.descuento_pct | Porcentaje recordado del chat |
| Estado pedido | MedusaJS API /admin/orders | Inferencia del historial |
| Disponibilidad envio | API transportadora | Estimacion del modelo |

## Si la API falla
1. Decir honestamente: "No puedo consultar el inventario ahora. Intenta en unos minutos."
2. NUNCA estimar o inventar un dato
3. Registrar el error en bot_audit_log

## Confirmacion en 2 pasos
TODA accion que modifica datos requiere confirmacion explicita SI/NO:
- Crear factura
- Registrar despacho
- Actualizar precio
- Asignar descuento
```

### 5.6 Skill: Accesibilidad

Archivo: `~/jarvis/projects/ecommerce-ciclismo/.opencode/skills/accesibilidad/SKILL.md`

```markdown
# Accesibilidad — Admin No Vidente

Reglas ABSOLUTAS para que el bot funcione perfectamente con lectores de pantalla y TTS.

## PROHIBIDO (nunca, bajo ninguna circunstancia)
- Tablas ASCII o tablas con columnas
- Emojis decorativos (bicicletas, checkmarks, etc.)
- Caracteres especiales que no se leen bien en TTS
- Imagenes sin descripcion textual
- Respuestas de mas de 10 lineas de texto
- Precios con simbolos: '$120.000' o '29.3k'

## OBLIGATORIO (siempre)
- Precios verbalizados: 'ciento veinte mil pesos'
- Stock verbalizado: 'cuarenta y siete unidades'
- Texto plano, lineas cortas
- Respuestas de maximo 10 lineas
- Verbalizable por TTS en menos de 15 segundos

## Ejemplo de respuesta correcta /stock
"Guante mtb corto Azul: cuarenta y siete unidades disponibles. Precio base: veintinueve mil trescientos veinticinco pesos."

## Ejemplo de respuesta incorrecta /stock
"| Guante MTB | 47 uds | $29.325 |"
```

### 5.7 Skill: Colombia Payments

Archivo: `~/jarvis/projects/ecommerce-ciclismo/.opencode/skills/colombia-payments/SKILL.md`

```markdown
# Colombia Payments — Pagos Colombianos

Eres experto en el ecosistema de pagos de Colombia. Integraciones Wompi y ePayco para MedusaJS v2.

## Metodos de pago priorizados
1. Nequi (via Wompi) — Alta penetracion, 0.9-1.5% comision
2. Bancolombia a la mano (via Wompi) — Alta penetracion, 1.5%
3. PSE debito bancario (via Wompi/ePayco) — Alta empresas, 0.8% + IVA
4. Tarjeta credito/debito (via Wompi) — Media, 2.5-3.5%
5. Efecty / Su Red (via ePayco) — Muy alta sin banco, 1.5-2%
6. Contraentrega (manual + n8n) — Alta desconfianza online

## Tres reglas del storefront para Colombia
1. Velocidad en 3G — carga < 3 segundos en red lenta
2. Checkout en un paso — direccion + pago + confirmacion sin paginar
3. Confianza visible — WhatsApp flotante, politica devolucion, sellos SSL/Wompi, NIT/RUT

## Modelo de negocio
- Setup fee inicial
- 3% por venta procesada
- Mantenimiento mensual

## Integracion MedusaJS
- Paquete: medusa-payment-wompi
- Configurar: CARD, NEQUI, PSE, BANCOLOMBIA_TRANSFER
- ePayco para: Efecty, Su Red, Baloto
```

### 5.8 Skill: Seguridad

Archivo: `~/jarvis/projects/ecommerce-ciclismo/.opencode/skills/seguridad/SKILL.md`

```markdown
# Seguridad — SecOps Silencioso

Eres el agente de seguridad. Operas en silencio, verificando cada request.

## Modelo asignado: fast (via LiteLLM)

## Stack de seguridad para desarrollo
- AgentSecOps/SecOpsAgentKit — 25+ skills, escanea cada PR
- TikiTribe/claude-secure-coding-rules — OWASP Top 10, CWE Top 25
- agamm/claude-code-owasp — Se activa automaticamente con frases clave

## Capas de seguridad en produccion
| Capa | Implementacion | Protege contra |
|------|---------------|---------------|
| Autenticacion | JWT 1h + refresh 7d | Acceso no autorizado |
| Rate limiting | 100 req/min por telegram_id | Abuso |
| Audit log | bot_audit_log (solo INSERT) | Fraude |
| Secretos | .env, NUNCA en codigo | Exposicion credenciales |
| N8N aislado | Solo via Nginx con SSL | Acceso no autorizado |
| Validacion entrada | Sanitizacion antes de API | SQL injection |

## Audit log schema
CREATE TABLE bot_audit_log (
  id SERIAL PRIMARY KEY,
  created_at TIMESTAMP DEFAULT NOW(),
  telegram_user VARCHAR(100),
  canal VARCHAR(20) CHECK (canal IN ('texto','voz','comando')),
  comando VARCHAR(50),
  input_texto TEXT,
  respuesta TEXT,
  api_endpoint VARCHAR(200),
  exitoso BOOLEAN,
  error_msg TEXT,
  agente VARCHAR(50)
);
-- INMUTABLE: solo INSERT. Nunca UPDATE ni DELETE.
```

---

## 6. Docker Compose — Produccion Ciclismo

Archivo: `~/jarvis/projects/ecommerce-ciclismo/docker-compose.yml`

```yaml
version: "3.9"

services:
  # ================================================================
  # MEDUSAJS v2 — Motor de ecommerce
  # ================================================================
  medusa:
    build:
      context: ./src/medusa
      dockerfile: Dockerfile
    container_name: ciclismo-medusa
    restart: unless-stopped
    ports:
      - "9000:9000"   # API admin
      - "7001:7001"   # Storefront API
    environment:
      - DATABASE_URL=postgresql://ciclismo:${DB_PASS}@postgres:5432/ciclismo
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET}
      - NODE_ENV=production
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started

  # ================================================================
  # BOT TELEGRAM — Interfaz del administrador
  # ================================================================
  bot:
    build:
      context: ./src/bot
      dockerfile: Dockerfile
    container_name: ciclismo-bot
    restart: unless-stopped
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - ADMIN_CHAT_ID=${ADMIN_CHAT_ID}
      - BODEGA_CHAT_ID=${BODEGA_CHAT_ID}
      - MEDUSA_API_URL=http://medusa:9000
      - LITELLM_URL=http://litellm:4000
      - LITELLM_KEY=${LITELLM_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=postgresql://ciclismo:${DB_PASS}@postgres:5432/ciclismo
      - REDIS_URL=redis://redis:6379
    depends_on:
      - medusa
      - litellm

  # ================================================================
  # STOREFRONT NEXT.JS — Tienda publica
  # ================================================================
  storefront:
    build:
      context: ./src/storefront
      dockerfile: Dockerfile
    container_name: ciclismo-storefront
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_MEDUSA_URL=http://medusa:9000
      - NEXT_PUBLIC_WOMPI_PUBLIC_KEY=${WOMPI_PUBLIC_KEY}
    depends_on:
      - medusa

  # ================================================================
  # LITELLM — Router de modelos
  # ================================================================
  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    container_name: ciclismo-litellm
    restart: unless-stopped
    ports:
      - "4000:4000"
    volumes:
      - ./litellm-config.yaml:/app/config.yaml
    environment:
      - LITELLM_MASTER_KEY=${LITELLM_KEY:-sk-jarvis-local}
      - OPENROUTER_API_KEY=${OPENROUTER_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_KEY:-}
    command: ["--config", "/app/config.yaml", "--port", "4000"]
    depends_on:
      - redis

  # ================================================================
  # POSTGRESQL — Fuente unica de verdad
  # ================================================================
  postgres:
    image: postgres:15-alpine
    container_name: ciclismo-postgres
    restart: unless-stopped
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=ciclismo
      - POSTGRES_USER=ciclismo
      - POSTGRES_PASSWORD=${DB_PASS}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ciclismo"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ================================================================
  # REDIS — Cache y lock de stock
  # ================================================================
  redis:
    image: redis:7-alpine
    container_name: ciclismo-redis
    restart: unless-stopped
    # Puerto NO expuesto — solo acceso interno

  # ================================================================
  # N8N — Automatizacion
  # ================================================================
  n8n:
    image: n8nio/n8n:latest
    container_name: ciclismo-n8n
    restart: unless-stopped
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASS}
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
      - WEBHOOK_URL=https://tiendaciclismo.co/n8n/
    volumes:
      - n8n_data:/home/node/.n8n

  # ================================================================
  # NGINX — Reverse proxy + SSL
  # ================================================================
  nginx:
    image: nginx:alpine
    container_name: ciclismo-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - medusa
      - storefront
      - n8n

  # ================================================================
  # MONITOR AGENT (JARVIS) — Vigila el VPS del cliente
  # ================================================================
  monitor:
    image: netdata/netdata:latest
    container_name: ciclismo-monitor
    restart: unless-stopped
    ports:
      - "19999:19999"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    cap_add:
      - SYS_PTRACE

  uptime:
    image: louislam/uptime-kuma:latest
    container_name: ciclismo-uptime
    restart: unless-stopped
    ports:
      - "3001:3001"
    volumes:
      - uptime_data:/app/data

volumes:
  postgres_data:
  n8n_data:
  uptime_data:
```

---

## 7. Obsidian Vault — Proyecto Ciclismo

### Estructura especifica del vault para este proyecto

```
~/jarvis/vault/
|
+-- 01-Proyectos/
|   +-- ecommerce-ciclismo.md         # Nota principal del proyecto
|
+-- 02-Agentes/
|   +-- Orquestador-Ciclismo.md
|   +-- Inventario-Ciclismo.md
|   +-- Ventas-Ciclismo.md
|   +-- Logistica-Ciclismo.md
|   +-- Ecommerce-Ciclismo.md
|   +-- Reportes-Ciclismo.md
|   +-- Seguridad-Ciclismo.md
|
+-- 03-Decisiones/
|   +-- ADR-005-medusajs-vs-shopify.md
|   +-- ADR-006-litellm-vs-openrouter-directo.md
|   +-- ADR-007-whisper-vs-stt-local.md
|   +-- ADR-008-wompi-vs-mercadopago.md
|
+-- 06-Clientes/
|   +-- ciclismo/
|       +-- infra.md                   # VPS, dominio, SSL
|       +-- pagos.md                   # Config Wompi, ePayco
|       +-- productos-608.md           # Inventario y precios
|       +-- deploys.md                # Log de deploys
```

### Nota principal del proyecto

Archivo: `~/jarvis/vault/01-Proyectos/ecommerce-ciclismo.md`

```markdown
# Ecommerce Ciclismo

**Estado**: En desarrollo
**Cliente**: Mayorista/minorista ciclismo Colombia
**Stack**: MedusaJS v2 + PostgreSQL + Redis + n8n + Bot Telegram + Whisper
**IA**: LiteLLM -> Ollama + OpenRouter (NO Claude Code directo)
**Admin**: NO VIDENTE — interfaz primaria: Bot Telegram + voz

## Progreso
- [x] Documentacion v3 completada
- [ ] Infraestructura Docker Compose
- [ ] MedusaJS v2 con 608 productos
- [ ] Bot Telegram con comandos + voz
- [ ] Sistema anti-alucinacion
- [ ] Pagos Colombia (Wompi + ePayco)
- [ ] Storefront Next.js
- [ ] N8N workflows
- [ ] Monitor Agent JARVIS
- [ ] Deploy a produccion

## Costos operativos (adaptados)
| Servicio | Costo/mes |
|---------|----------|
| OpenRouter (via LiteLLM) | $5-15 |
| Ollama local (desarrollo) | $0 |
| Whisper STT | $2-5 |
| VPS produccion | $30-60 |
| Backblaze B2 | <$0.10 |
| Cloudflare | $0 |
| **TOTAL** | **$37-80** |

## Modelos via LiteLLM
- Orquestador/Ventas/Ecommerce -> `coder` (Qwen3 Coder 30B / Sonnet)
- Inventario/Logistica/Seguridad -> `fast` (Qwen2.5 Coder 7B / Haiku)
- Reportes -> `thinker` (DeepSeek R1)
- Premium -> `premium` (solo emergencia)

## Relacionado
- [[ADR-005-medusajs-vs-shopify]]
- [[ADR-006-litellm-vs-openrouter-directo]]
- [[ciclismo/infra]]
```

---

## 8. OpenCode Config — Proyecto Ciclismo

Archivo: `~/jarvis/projects/ecommerce-ciclismo/.opencode/config.json`

```json
{
  "provider": {
    "base_url": "http://localhost:4000",
    "api_key": "sk-jarvis-local",
    "default_model": "coder"
  },
  "skills": {
    "paths": [
      "./.opencode/skills/orquestador",
      "./.opencode/skills/inventario",
      "./.opencode/skills/ventas",
      "./.opencode/skills/logistica",
      "./.opencode/skills/ecommerce",
      "./.opencode/skills/reportes",
      "./.opencode/skills/seguridad",
      "./.opencode/skills/accesibilidad",
      "./.opencode/skills/colombia-payments",
      "./.opencode/skills/anti-hallucination"
    ],
    "auto_discover": true,
    "lazy_load": true
  },
  "mcp": {
    "servers": {
      "n8n": {
        "command": "npx",
        "args": ["-y", "mcp-n8n"],
        "env": {
          "N8N_URL": "http://localhost:5678"
        }
      },
      "docker": {
        "command": "npx",
        "args": ["-y", "mcp-docker"]
      },
      "postgres": {
        "command": "npx",
        "args": ["-y", "mcp-postgres"],
        "env": {
          "DB_URL": "postgresql://ciclismo:ciclismo2026@localhost:5432/ciclismo"
        }
      },
      "filesystem": {
        "command": "npx",
        "args": ["-y", "mcp-filesystem", "."]
      },
      "github": {
        "command": "npx",
        "args": ["-y", "mcp-github"]
      },
      "obsidian": {
        "command": "npx",
        "args": ["-y", "mcp-obsidian"],
        "env": {
          "OBSIDIAN_VAULT_PATH": "/home/user/jarvis/vault"
        }
      }
    }
  }
}
```

---

## 9. Plan de Ejecucion — Semana a Semana

### Semana 1: Infraestructura Base

```
Tareas (respetando JARVIS v2):
1. docker compose up — MedusaJS v2 + PostgreSQL + Redis + n8n
2. LiteLLM con config especifica ciclismo
3. Ollama con modelos: qwen2.5-coder:7b, gemma2:2b, nomic-embed-text
4. Crear proyecto en JARVIS: jarvis-init.sh "Ecommerce Ciclismo"
5. Inicializar repo Git: git-setup.sh ecommerce-ciclismo
6. Crear nota en Obsidian vault
7. Cargar 608 productos en MedusaJS
8. Nginx + SSL Certbot

Agente lider: Backend Agent (skill: backend)
Modelo: coder (via LiteLLM)
Commit: feat(infra): MedusaJS v2 + PostgreSQL + Redis + n8n [agent:backend]
```

### Semana 2: Bot Telegram + Voz + Anti-Alucinacion

```
Tareas:
1. Implementar todos los comandos del bot (seccion 4.2 del doc)
2. Handler de voz con Whisper API
3. Sistema anti-alucinacion: fuente unica de verdad
4. Audit log inmutable (bot_audit_log)
5. Reglas de accesibilidad admin no vidente
6. Test: cada comando con respuestas verbalizadas

Agente lider: Backend Agent (skill: backend) + QA Agent (skill: qa)
Modelo dev: coder | Modelo test: thinker
Commit: feat(bot): Telegram commands + Whisper + anti-hallucination [agent:backend]
```

### Semana 3: Pagos Colombia + Storefront

```
Tareas:
1. Integrar Wompi (Nequi, PSE, Bancolombia, tarjetas)
2. Integrar ePayco (Efecty, Su Red, Baloto)
3. Next.js storefront con checkout Colombia en un paso
4. Actualizar 32 precios pendientes
5. Test: flujo completo de compra

Agente lider: Frontend Agent (skill: frontend)
Modelo: coder
Commit: feat(payments): Wompi + ePayco + storefront checkout [agent:frontend]
```

### Semana 4: N8N + Monitor + Deploy

```
Tareas:
1. N8N: alerta stock critico automatica
2. N8N: confirmacion pedido al cliente
3. N8N: flujo contraentrega
4. N8N: backup diario + notificacion al bot
5. Monitor Agent JARVIS en VPS
6. Deploy a produccion: jarvis-deploy.sh ecommerce-ciclismo user@vps
7. Verificar Monitor Agent activo

Agente lider: DevOps Agent (skill: devops) + Monitor Agent (skill: monitor)
Modelo: fast
Commit: deploy(prod): v1.0.0 ecommerce ciclismo [agent:devops]
```

---

## 10. Comandos de Inicio

```bash
# ================================================================
# INICIO RAPIDO — Ecommerce Ciclismo con JARVIS v2
# ================================================================

# 1. Crear el proyecto en JARVIS
cd ~/jarvis
bash scripts/jarvis-init.sh "Ecommerce Ciclismo" "Mayorista/minorista ciclismo Colombia"

# 2. Entrar al proyecto
cd ~/jarvis/projects/ecommerce-ciclismo

# 3. Crear estructura de skills del proyecto
mkdir -p .opencode/skills/{orquestador,inventario,ventas,logistica,ecommerce,reportes,seguridad,accesibilidad,colombia-payments,anti-hallucination}

# 4. Crear los SKILL.md (copiar de seccion 5 de este documento)
# ... crear cada archivo ...

# 5. Validar skills
bash ~/jarvis/skills/autoskills.sh validate

# 6. Crear .env
cp .env.example .env
nano .env  # Rellenar con: OPENROUTER_KEY, TELEGRAM_BOT_TOKEN, etc.

# 7. Levantar Docker Compose del proyecto
docker compose up -d

# 8. Descargar modelos Ollama para desarrollo
docker exec jarvis-ollama ollama pull qwen2.5-coder:7b
docker exec jarvis-ollama ollama pull gemma2:2b
docker exec jarvis-ollama ollama pull nomic-embed-text

# 9. Abrir OpenCode y empezar a construir
opencode

# 10. Primer prompt sugerido:
# "Lee los skills del proyecto. Construye la infraestructura base:
#  MedusaJS v2 + PostgreSQL + Redis + n8n en Docker Compose.
#  Usa las reglas del skill orquestador. Admin es no vidente."
```

---

## Apéndice: Cambios especificos vs documento original

| # | En el doc original | En JARVIS v2 | Razon |
|---|-------------------|-------------|-------|
| 1 | `ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'` | LiteLLM en `http://localhost:4000` | Centralizacion + failover + cost tracking |
| 2 | `ANTHROPIC_API_KEY='sk-or-tu-key'` | `LITELLM_KEY='sk-jarvis-local'` | Una sola key para todos los modelos |
| 3 | `claude` (CLI directo) | `opencode` (CLI con LiteLLM) | OpenCode soporta skills + MCP |
| 4 | `antigravity init --project ciclismo` | Obsidian vault + Qdrant | Memoria persistente en archivos .md |
| 5 | `antigravity sync --watch` | `sync_obsidian.sh` (cron) | Indexado automatico del vault |
| 6 | `.claude/agents/*.md` | `.opencode/skills/*/SKILL.md` | Formato estandar de Agent Skills |
| 7 | `.claude/skills/owasp-security/` | `.opencode/skills/seguridad/SKILL.md` | Mismo contenido, diferente path |
| 8 | Claude Sonnet 4.5 para todo | `coder`/`fast`/`thinker` segun tarea | Ahorro 73% en modelos |
| 9 | Claude Haiku para simples | Ollama local primero, Haiku como failover | $0 cuando Ollama funciona |
| 10 | `CLAUDE.md` como archivo maestro | `SKILL.md` por agente + Obsidian vault | Distribuido + buscable |
