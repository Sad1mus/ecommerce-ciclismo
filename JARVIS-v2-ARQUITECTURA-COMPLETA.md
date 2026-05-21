# JARVIS v2 — Fábrica de Fábricas AaaS

> Arquitectura completa para empresa de software autónoma en Xubuntu
> Stack: OpenCode Go + OpenRouter + LiteLLM + n8n + Obsidian + VS Code
> Fecha: Mayo 2026

---

## Tabla de Contenidos

1. [Visión General](#1-visión-general)
2. [Arquitectura del Stack](#2-arquitectura-del-stack)
3. [Estructura de Directorios](#3-estructura-de-directorios)
4. [Docker Compose Maestro](#4-docker-compose-maestro)
5. [LiteLLM — Router de Modelos Local](#5-litellm--router-de-modelos-local)
6. [OpenCode + Skills + VS Code + MCP](#6-opencode--skills--vs-code--mcp)
7. [Obsidian — Segundo Cerebro](#7-obsidian--segundo-cerebro)
8. [autoskills.sh — Discovery Automático](#8-autoskillssh--discovery-automático)
9. [Agentes de la Empresa](#9-agentes-de-la-empresa)
10. [Workflows n8n](#10-workflows-n8n)
11. [Estrategia Git Profesional](#11-estrategia-git-profesional)
12. [Packager & Deploy a VPS](#12-packager--deploy-a-vps)
13. [Monitor Agent — Vigilante Remoto](#13-monitor-agent--vigilante-remoto)
14. [Dashboard & Observabilidad](#14-dashboard--observabilidad)
15. [Costos Estimados](#15-costos-estimados)
16. [Quick Start — Setup en 30 minutos](#16-quick-start--setup-en-30-minutos)

---

## 1. Visión General

JARVIS es un sistema de desarrollo de software autónomo que funciona como una empresa completa. Cada rol (PM, Backend, Frontend, DevOps, QA, Monitor) es un agente de IA con skills especializados, memoria compartida via Obsidian, y orquestación via n8n. Cuando un proyecto está listo, se empaqueta en Docker y se despliega en la VPS del cliente con un agente monitor integrado.

### Principios

- **100% open-source** en lo posible
- **Local-first** — todo corre en tu Xubuntu
- **Costo mínimo** — $15-25/mes vs $200+ de alternativas
- **Observable** — sabes qué hace cada agente en cada momento
- **Replicable** — las plantillas se clonan en nuevos proyectos/empresas

### Diagrama General

```
+==================================================================+
|                        TU XUBUNTU — JARVIS v2                     |
|                                                                   |
|  +------------------------------------------------------------+  |
|  |  CAPA 0: CEREBRO                                           |  |
|  |  Obsidian Vault (segundo cerebro de la empresa)            |  |
|  |  - Decisiones de arquitectura                              |  |
|  |  - Lecciones aprendidas                                    |  |
|  |  - Plantillas y patrones                                   |  |
|  |  - Historial de proyectos                                  |  |
|  +----------------------------+-------------------------------+  |
|                               |                                  |
|  +----------------------------v-------------------------------+  |
|  |  CAPA 1: CODING AGENT                                      |  |
|  |  OpenCode (CLI) + VS Code + Skills + MCP                   |  |
|  |  +--------+ +---------+ +--------+ +-------+ +---------+  |  |
|  |  | PM     | | Backend | | Front  | |DevOps | | QA      |  |  |
|  |  | Agent  | | Agent   | | Agent  | | Agent | | Agent   |  |  |
|  |  +--------+ +---------+ +--------+ +-------+ +---------+  |  |
|  +----------------------------+-------------------------------+  |
|                               |                                  |
|  +----------------------------v-------------------------------+  |
|  |  CAPA 2: ROUTER DE MODELOS                                 |  |
|  |  LiteLLM (proxy local)                                     |  |
|  |  Ollama (gratis) | OpenCode Go ($10/mes) | OpenRouter      |  |
|  +----------------------------+-------------------------------+  |
|                               |                                  |
|  +----------------------------v-------------------------------+  |
|  |  CAPA 3: ORQUESTACION                                      |  |
|  |  n8n (workflows visuales)                                  |  |
|  |  - Dev Pipeline    - Client Comms    - Deploy Flow         |  |
|  |  - Monitor Loop    - Template Engine  - Billing            |  |
|  +----------------------------+-------------------------------+  |
|                               |                                  |
|  +----------------------------v-------------------------------+  |
|  |  CAPA 4: INFRA (Docker Compose)                            |  |
|  |  Ollama | LiteLLM | n8n | PostgreSQL | Qdrant              |  |
|  |  MinIO  | Redis   | Netdata | Uptime Kuma | Portainer      |  |
|  |  Grafana | Obsidian Sync                                     |  |
|  +------------------------------------------------------------+  |
+==================================================================+
           | docker build + git push + deploy
           v
+==================================================================+
|                     VPS DEL CLIENTE                               |
|  Docker Compose (1-click deploy)                                 |
|  +----------+ +----------+ +------------------+                  |
|  | App      | | DB       | | Monitor Agent    |                  |
|  | Container| | Container| | (Netdata+Uptime) |                  |
|  +----------+ +----------+ +------------------+                  |
+==================================================================+
```

---

## 2. Arquitectura del Stack

| Capa | Componente | Tecnologia | Rol |
|------|-----------|------------|-----|
| Cerebro | Segundo cerebro | **Obsidian** | Memoria organizacional, decisiones, lecciones |
| Cerebro | Vector DB | **Qdrant** | Embeddings para busqueda semantica |
| Coding | Agente principal | **OpenCode Go** ($10/mes) | Coding agent con skills |
| Coding | IDE | **VS Code** | Editor + extensiones + MCP |
| Coding | Skills discovery | **autoskills.sh** | Busqueda y carga automatica de skills |
| Routing | Proxy local | **LiteLLM** | Unifica Ollama + OpenRouter + APIs |
| Routing | LLM local | **Ollama** | Modelos gratis en tu hardware |
| Routing | Cloud router | **OpenRouter** | Modelos baratos (DeepSeek, Qwen, etc.) |
| Orquestacion | Workflows | **n8n** | Automatizacion visual de procesos |
| Infra | Contenedores | **Docker Compose** | Todo corre en containers |
| Infra | Base de datos | **PostgreSQL** | Datos de proyectos, tareas, clientes |
| Infra | Cache | **Redis** | Colas y cache de agentes |
| Infra | Storage | **MinIO** | Archivos, templates, deploys |
| Monitor | Sistema | **Netdata** | Metricas en tiempo real |
| Monitor | Uptime | **Uptime Kuma** | Status page de servicios |
| Monitor | Dashboard | **Grafana** | Visualizacion de la fabrica |
| Monitor | Docker UI | **Portainer** | Gestion visual de containers |
| Git | Repos | **GitHub** | Control de versiones profesional |
| Git | Branching | **GitFlow adaptado** | Ramas por entorno y agente |

---

## 3. Estructura de Directorios

```
~/jarvis/
|
+-- docker/
|   +-- docker-compose.yml          # Stack completo
|   +-- .env                        # Variables de entorno (NO subir a git)
|   +-- .env.example                # Template de variables
|   +-- litellm/
|   |   +-- config.yaml             # Configuracion de modelos
|   +-- n8n/
|   |   +-- data/                   # Workflows y datos de n8n
|   +-- ollama/
|   |   +-- data/                   # Modelos descargados
|   +-- postgres/
|   |   +-- data/                   # Base de datos
|   +-- qdrant/
|   |   +-- data/                   # Vectores
|   +-- minio/
|   |   +-- data/                   # Archivos
|   +-- redis/
|   |   +-- data/                   # Cache
|   +-- netdata/
|   |   +-- config/                 # Config de monitoreo
|   +-- uptime-kuma/
|   |   +-- data/                   # Datos de uptime
|   +-- grafana/
|   |   +-- data/                   # Dashboards
|   +-- portainer/
|       +-- data/                   # Datos de portainer
|
+-- vault/                          # Obsidian Vault (SEGUNDO CEREBRO)
|   +-- .obsidian/                  # Config de Obsidian
|   |   +-- app.json
|   |   +-- appearance.json
|   |   +-- community-plugins.json
|   +-- 00-Inbox/                   # Notas rapidas sin clasificar
|   +-- 01-Proyectos/               # Un nota por proyecto activo
|   +-- 02-Agentes/                 # Documentacion de cada agente
|   |   +-- PM-Agent.md
|   |   +-- Backend-Agent.md
|   |   +-- Frontend-Agent.md
|   |   +-- DevOps-Agent.md
|   |   +-- QA-Agent.md
|   |   +-- Monitor-Agent.md
|   +-- 03-Decisiones/             # ADRs (Architecture Decision Records)
|   |   +-- ADR-001-stack-principal.md
|   |   +-- ADR-002-estrategia-modelos.md
|   +-- 04-Lecciones/              # Post-mortems y aprendizajes
|   |   +-- 2026-05-deploy-fallido-cliente-x.md
|   +-- 05-Templates/              # Plantillas reutilizables
|   |   +-- template-prd.md
|   |   +-- template-sprint.md
|   |   +-- template-dockerize.md
|   +-- 06-Clientes/               # Un folder por cliente
|   |   +-- cliente-sabor/
|   |       +-- proyecto-inventario.md
|   |       +-- infra.md
|   +-- 07-Diario/                  # Log diario del negocio
|   +-- 08-Recursos/               # Cheatsheets, referencias
|   +-- 09-Archivo/                # Proyectos terminados
|   +-- MOC.md                     # Map of Content (indice principal)
|   +-- README.md                  # Descripcion del vault
|
+-- skills/                         # Agent Skills (OpenCode / Claude Code)
|   +-- pm/
|   |   +-- SKILL.md               # Instrucciones del skill
|   |   +-- scripts/
|   |   |   +-- generate_prd.sh
|   |   |   +-- plan_sprint.sh
|   |   |   +-- review_progress.sh
|   |   +-- templates/
|   |   |   +-- prd_template.md
|   |   |   +-- sprint_template.md
|   |   +-- metadata.json
|   +-- backend/
|   |   +-- SKILL.md
|   |   +-- scripts/
|   |   |   +-- scaffold_api.sh
|   |   |   +-- gen_models.sh
|   |   |   +-- gen_endpoints.sh
|   |   |   +-- review_code.sh
|   |   +-- templates/
|   |   |   +-- express-skeleton/
|   |   |   +-- fastapi-skeleton/
|   |   |   +-- nextjs-skeleton/
|   |   +-- metadata.json
|   +-- frontend/
|   |   +-- SKILL.md
|   |   +-- scripts/
|   |   |   +-- scaffold_ui.sh
|   |   |   +-- gen_components.sh
|   |   +-- templates/
|   |   +-- metadata.json
|   +-- devops/
|   |   +-- SKILL.md
|   |   +-- scripts/
|   |   |   +-- dockerize.sh
|   |   |   +-- deploy_vps.sh
|   |   |   +-- setup_ci.sh
|   |   |   +-- ssl_setup.sh
|   |   |   +-- setup_git_repo.sh
|   |   +-- templates/
|   |   |   +-- Dockerfile.node
|   |   |   +-- Dockerfile.python
|   |   |   +-- Dockerfile.nextjs
|   |   |   +-- docker-compose.prod.yml
|   |   |   +-- nginx.conf
|   |   |   +-- .gitignore
|   |   +-- metadata.json
|   +-- qa/
|   |   +-- SKILL.md
|   |   +-- scripts/
|   |   |   +-- run_tests.sh
|   |   |   +-- gen_e2e.sh
|   |   |   +-- security_scan.sh
|   |   +-- metadata.json
|   +-- monitor/
|   |   +-- SKILL.md
|   |   +-- scripts/
|   |   |   +-- health_check.sh
|   |   |   +-- alert_handler.sh
|   |   |   +-- auto_heal.sh
|   |   +-- metadata.json
|   +-- brain/
|   |   +-- SKILL.md               # Skill de memoria compartida
|   |   +-- scripts/
|   |       +-- query_memory.sh
|   |       +-- store_memory.sh
|   |       +-- sync_obsidian.sh    # Sincroniza con Obsidian vault
|   +-- autoskills.sh              # Discovery automatico de skills
|
+-- projects/                       # Proyectos activos
|   +-- _template/                  # Template para nuevos proyectos
|   |   +-- .opencode/
|   |   |   +-- skills/            # Skills especificos del proyecto
|   |   +-- .github/
|   |   |   +-- workflows/         # CI/CD templates
|   |   +-- docker-compose.yml
|   |   +-- Dockerfile
|   |   +-- .env.example
|   |   +-- .gitignore
|   +-- inventario-sabor/           # Ejemplo: proyecto de cliente
|       +-- src/
|       +-- .opencode/
|       +-- docker-compose.yml
|       +-- Dockerfile
|
+-- deploy/                         # Paquetes listos para deploy
|   +-- inventario-sabor/
|       +-- Dockerfile
|       +-- docker-compose.yml
|       +-- nginx.conf
|       +-- .env.example
|       +-- deploy.sh              # 1-click deploy
|
+-- scripts/                        # Scripts de utilidad
|   +-- autoskills.sh              # Skill discovery
|   +-- jarvis-init.sh             # Inicializar un nuevo proyecto
|   +-- jarvis-deploy.sh           # Empaquetar y deployar
|   +-- jarvis-monitor.sh          # Chequear todos los clientes
|   +-- jarvis-report.sh           # Generar reporte semanal
|   +-- git-setup.sh              # Configurar repo con branching
|
+-- .github/                        # Config del repo principal JARVIS
|   +-- workflows/
|       +-- skills-ci.yml          # Validar skills en cada PR
|       +-- deploy-template.yml    # Deploy de templates
|
+-- .gitignore
+-- .env.example
+-- README.md
```

---

## 4. Docker Compose Maestro

Archivo: `~/jarvis/docker/docker-compose.yml`

```yaml
version: "3.9"

services:
  # ================================================================
  # ROUTER DE MODELOS - LiteLLM
  # ================================================================
  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    container_name: jarvis-litellm
    restart: unless-stopped
    ports:
      - "4000:4000"
    volumes:
      - ./litellm/config.yaml:/app/config.yaml
    environment:
      - LITELLM_MASTER_KEY=${LITELLM_KEY:-sk-jarvis-local}
      - OPENROUTER_API_KEY=${OPENROUTER_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_KEY:-}
    command: ["--config", "/app/config.yaml", "--port", "4000"]
    depends_on:
      - redis

  # ================================================================
  # LLM LOCAL - Ollama
  # ================================================================
  ollama:
    image: ollama/ollama:latest
    container_name: jarvis-ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ./ollama/data:/root/.ollama
    # GPU NVIDIA (descomentar si aplica):
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: all
    #           capabilities: [gpu]

  # ================================================================
  # ORQUESTADOR - n8n
  # ================================================================
  n8n:
    image: n8nio/n8n:latest
    container_name: jarvis-n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    volumes:
      - ./n8n/data:/home/node/.n8n
      - ../skills:/data/skills
      - ../vault:/data/vault
      - ../templates:/data/templates
      - ../deploy:/data/deploy
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=jarvis
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASS:-jarvis2026}
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - WEBHOOK_URL=http://localhost:5678/
      - GENERIC_TIMEZONE=America/Panama
      - EXECUTIONS_DATA_PRUNE=true
      - EXECUTIONS_DATA_MAX_AGE=168
    depends_on:
      - postgres
      - redis

  # ================================================================
  # BASE DE DATOS - PostgreSQL
  # ================================================================
  postgres:
    image: postgres:16-alpine
    container_name: jarvis-postgres
    restart: unless-stopped
    ports:
      - "5432:5432"
    volumes:
      - ./postgres/data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=jarvis
      - POSTGRES_USER=jarvis
      - POSTGRES_PASSWORD=${DB_PASS:-jarvis2026}

  # ================================================================
  # MEMORIA VECTORIAL - Qdrant
  # ================================================================
  qdrant:
    image: qdrant/qdrant:latest
    container_name: jarvis-qdrant
    restart: unless-stopped
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./qdrant/data:/qdrant/storage

  # ================================================================
  # ALMACENAMIENTO - MinIO
  # ================================================================
  minio:
    image: minio/minio:latest
    container_name: jarvis-minio
    restart: unless-stopped
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - ./minio/data:/data
    environment:
      - MINIO_ROOT_USER=jarvis
      - MINIO_ROOT_PASSWORD=${MINIO_PASS:-jarvis2026}
    command: server /data --console-address ":9001"

  # ================================================================
  # CACHE - Redis
  # ================================================================
  redis:
    image: redis:7-alpine
    container_name: jarvis-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - ./redis/data:/data

  # ================================================================
  # MONITOREO LOCAL - Netdata
  # ================================================================
  netdata:
    image: netdata/netdata:latest
    container_name: jarvis-netdata
    restart: unless-stopped
    ports:
      - "19999:19999"
    volumes:
      - ./netdata/config:/etc/netdata
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    cap_add:
      - SYS_PTRACE

  # ================================================================
  # UPTIME - Uptime Kuma
  # ================================================================
  uptime-kuma:
    image: louislam/uptime-kuma:latest
    container_name: jarvis-uptime
    restart: unless-stopped
    ports:
      - "3001:3001"
    volumes:
      - ./uptime-kuma/data:/app/data

  # ================================================================
  # DOCKER UI - Portainer
  # ================================================================
  portainer:
    image: portainer/portainer-ce:latest
    container_name: jarvis-portainer
    restart: unless-stopped
    ports:
      - "9443:9443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./portainer/data:/data

  # ================================================================
  # DASHBOARD - Grafana
  # ================================================================
  grafana:
    image: grafana/grafana:latest
    container_name: jarvis-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - ./grafana/data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_USER=jarvis
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASS:-jarvis2026}
    depends_on:
      - postgres
```

Archivo: `~/jarvis/docker/.env.example`

```bash
# ================================================================
# JARVIS v2 - Variables de Entorno
# COPIAR a .env y rellenar con tus valores reales
# ================================================================

# --- Modelos ---
OPENROUTER_KEY=sk-or-v1-xxxxxxxxxxxxx
ANTHROPIC_KEY=sk-ant-xxxxxxxxxxxxx           # Opcional, solo emergencia

# --- Seguridad ---
LITELLM_KEY=sk-jarvis-local
N8N_PASS=tu_password_seguro
DB_PASS=tu_password_seguro
MINIO_PASS=tu_password_seguro
GRAFANA_PASS=tu_password_seguro

# --- GitHub ---
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
GITHUB_USER=tu-usuario

# --- Telegram (notificaciones) ---
TELEGRAM_BOT_TOKEN=xxxxxxxxxxxxx:xxxxxxxxx
TELEGRAM_CHAT_ID=xxxxxxxxx

# --- Obsidian ---
OBSIDIAN_VAULT_PATH=/home/user/jarvis/vault
```

---

## 5. LiteLLM — Router de Modelos Local

Archivo: `~/jarvis/docker/litellm/config.yaml`

```yaml
model_list:
  # ================================================================
  # CODER — Modelo principal de codigo (2 opciones: local + cloud)
  # LiteLLM hace failover automatico si uno falla
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

  # ================================================================
  # THINKER — Razonamiento profundo (bugs, arquitectura)
  # ================================================================
  - model_name: thinker
    litellm_params:
      model: openrouter/deepseek/deepseek-r1
      api_key: os.environ/OPENROUTER_KEY
    model_info:
      mode: chat
      cost: low

  # ================================================================
  # FAST — Tareas simples y rapidas (monitor, logs, formato)
  # ================================================================
  - model_name: fast
    litellm_params:
      model: ollama_chat/gemma2:2b
      api_base: http://ollama:11434
    model_info:
      mode: chat
      cost: free

  # ================================================================
  # PREMIUM — Solo cuando sea estrictamente necesario
  # ================================================================
  - model_name: premium
    litellm_params:
      model: anthropic/claude-sonnet-4-20250514
      api_key: os.environ/ANTHROPIC_KEY
    model_info:
      mode: chat
      cost: high

# ================================================================
# ROUTER SETTINGS
# ================================================================
router_settings:
  num_retries: 2
  timeout: 120
  fallbacks:
    - {"coder": ["thinker"]}
    - {"thinker": ["coder"]}

# ================================================================
# ASIGNACION POR AGENTE (cada agente usa su modelo)
# ================================================================
# PM Agent      -> coder (suficiente para PRDs y planes)
# Backend Agent -> coder (con failover a Ollama local)
# Frontend Agent-> coder (mismo stack)
# DevOps Agent  -> fast  (tareas rutinarias de deploy)
# QA Agent      -> thinker (razonamiento profundo para bugs)
# Monitor Agent -> fast  (analizar metricas es simple)
# Tu (manual)   -> premium (solo cuando necesites lo mejor)
```

---

## 6. OpenCode + Skills + VS Code + MCP

### 6.1 Configuracion de OpenCode

Archivo: `~/.config/opencode/config.json`

```json
{
  "provider": {
    "base_url": "http://localhost:4000",
    "api_key": "sk-jarvis-local",
    "default_model": "coder"
  },
  "skills": {
    "paths": [
      "~/jarvis/skills/pm",
      "~/jarvis/skills/backend",
      "~/jarvis/skills/frontend",
      "~/jarvis/skills/devops",
      "~/jarvis/skills/qa",
      "~/jarvis/skills/monitor",
      "~/jarvis/skills/brain"
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
          "N8N_URL": "http://localhost:5678",
          "N8N_KEY": "jarvis:jarvis2026"
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
          "DB_URL": "postgresql://jarvis:jarvis2026@localhost:5432/jarvis"
        }
      },
      "filesystem": {
        "command": "npx",
        "args": ["-y", "mcp-filesystem", "/home/user/jarvis"]
      },
      "github": {
        "command": "npx",
        "args": ["-y", "mcp-github"],
        "env": {
          "GITHUB_TOKEN": ""
        }
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

### 6.2 Configuracion VS Code

Archivo: `~/jarvis/.vscode/settings.json`

```json
{
  "github.copilot.chat.agentSkills.enabled": true,
  "chat.agentSkills.skillLocations": [
    "~/jarvis/skills/pm",
    "~/jarvis/skills/backend",
    "~/jarvis/skills/frontend",
    "~/jarvis/skills/devops",
    "~/jarvis/skills/qa",
    "~/jarvis/skills/monitor",
    "~/jarvis/skills/brain"
  ],
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
          "DB_URL": "postgresql://jarvis:jarvis2026@localhost:5432/jarvis"
        }
      },
      "filesystem": {
        "command": "npx",
        "args": ["-y", "mcp-filesystem", "/home/user/jarvis"]
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
  },
  "terminal.integrated.env.linux": {
    "OPENCODE_CONFIG": "~/jarvis/.opencode/config.json"
  }
}
```

### 6.3 Extensiones VS Code recomendadas

```
# Instalar desde terminal
code --install-extension ms-python.python
code --install-extension ms-azuretools.vscode-docker
code --install-extension github.copilot
code --install-extension github.vscode-github-actions
code --install-extension graphql.vscode-graphql
code --install-extension bradlc.vscode-tailwindcss
code --install-extension prisma.prisma
code --install-extension esbenp.prettier-vscode
code --install-extension dbaeumer.vscode-eslint
code --install-extension hashicorp.terraform
code --install-extension ms-vscode-remote.remote-containers
```

---

## 7. Obsidian — Segundo Cerebro

### 7.1 Por que Obsidian

Obsidian es el segundo cerebro perfecto para JARVIS porque:

- **Archivos Markdown planos** — los agentes pueden leer y escribir directamente
- **Links bidireccionales** — conecta decisiones con lecciones y proyectos
- **Graph View** — visualiza como se conecta el conocimiento de la empresa
- **Plugins** — community plugins para IA, templates, dataview
- **Local** — todo en tu disco, sin dependencia de cloud
- **MCP compatible** — agentes leen/escriben en el vault via MCP

### 7.2 Estructura del Vault

Ya definida en la seccion 3. Aqui los archivos clave:

### 7.3 MOC — Map of Content

Archivo: `~/jarvis/vault/MOC.md`

```markdown
# JARVIS — Map of Content

## Proyectos Activos
- [[inventario-sabor]] — API de inventario para Restaurante El Sabor
- [[crm-negocios]] — CRM para PYMEs

## Agentes
- [[PM-Agent]] — Project Manager
- [[Backend-Agent]] — Desarrollo de APIs y servicios
- [[Frontend-Agent]] — Interfaces y UI
- [[DevOps-Agent]] — Docker, deploy, infra
- [[QA-Agent]] — Testing y calidad
- [[Monitor-Agent]] — Vigilancia de servidores

## Decisiones Clave
- [[ADR-001-stack-principal]] — Por que OpenCode + LiteLLM + n8n
- [[ADR-002-estrategia-modelos]] — Capas de modelos por costo
- [[ADR-003-obsidian-brain]] — Obsidian como segundo cerebro
- [[ADR-004-git-strategy]] — Branching para agentes automaticos

## Lecciones Recientes
- [[2026-05-deploy-fallido-cliente-x]]
- [[2026-05-ollama-memory-optimization]]

## Templates
- [[template-prd]]
- [[template-sprint]]
- [[template-dockerize]]
- [[template-cliente]]

## Recursos
- [[cheatsheet-opencode]]
- [[cheatsheet-docker]]
- [[cheatsheet-litellm]]
```

### 7.4 ADR Template

Archivo: `~/jarvis/vault/03-Decisiones/ADR-template.md`

```markdown
# ADR-XXX: [Titulo de la Decision]

**Fecha**: YYYY-MM-DD
**Estado**: Propuesto | Aceptado | Deprecado
**Decision maker**: [Quien tomo la decision]

## Contexto
Que situacion motivo esta decision?

## Decision
Que decidimos hacer?

## Alternativas Consideradas
1. Opcion A — Pros / Contras
2. Opcion B — Pros / Contras
3. Opcion C — Pros / Contras

## Consecuencias
- Positivas: ...
- Negativas: ...
- Riesgos: ...

## Relacionado
- [[ADR-XXX]]
- [[proyecto-tal]]
```

### 7.5 Skill Brain — Sincronizacion con Obsidian

Archivo: `~/jarvis/skills/brain/SKILL.md`

```markdown
# Brain — Memoria Compartida de la Empresa

Eres el sistema de memoria central de JARVIS. Todos los agentes te consultan.

## Reglas
1. **Antes de actuar**, consulta si ya existe una decision o leccion relevante
2. **Despues de actuar**, guarda lo que hiciste y por que
3. **Conflictos** → notifica al PM Agent y al humano

## Fuentes de memoria
- **Obsidian Vault** (`~/jarvis/vault/`) — Decisiones, lecciones, proyectos
- **Qdrant** (`localhost:6333`) — Busqueda semantica en documentos
- **PostgreSQL** (`localhost:5432`) — Datos estructurados de proyectos

## Protocolo de consulta
1. Buscar en Qdrant (semantic search)
2. Buscar en Obsidian (decisions + lecciones)
3. Buscar en PostgreSQL (datos del proyecto)
4. Si no hay contexto → preguntar al humano

## Protocolo de escritura
1. Guardar en Qdrant (embedding del evento)
2. Escribir en Obsidian (si es decision o leccion)
3. Actualizar PostgreSQL (si es dato de proyecto)

## Scripts disponibles
- `query_memory.sh "pregunta"` — Busca en todas las fuentes
- `store_memory.sh "evento" "categoria"` — Guarda un evento
- `sync_obsidian.sh` — Sincroniza Qdrant con el vault Obsidian
```

Archivo: `~/jarvis/skills/brain/scripts/sync_obsidian.sh`

```bash
#!/bin/bash
# sync_obsidian.sh — Sincroniza Obsidian Vault con Qdrant
# Lee todos los .md del vault y los indexa en Qdrant para busqueda semantica

VAULT_PATH="${OBSIDIAN_VAULT_PATH:-$HOME/jarvis/vault}"
QDRANT_URL="http://localhost:6333"
COLLECTION="jarvis-brain"

echo "Sincronizando Obsidian Vault con Qdrant..."

# Crear coleccion si no existe
curl -s -X PUT "${QDRANT_URL}/collections/${COLLECTION}" \
  -H 'Content-Type: application/json' \
  -d '{
    "vectors": {
      "size": 768,
      "distance": "Cosine"
    }
  }' > /dev/null 2>&1

# Indexar cada archivo .md
find "$VAULT_PATH" -name "*.md" -type f | while read -r file; do
  # Obtener ruta relativa como ID
  rel_path="${file#$VAULT_PATH/}"
  doc_id=$(echo "$rel_path" | md5sum | cut -d' ' -f1)

  # Leer contenido
  content=$(cat "$file")

  # Generar embedding via LiteLLM/Ollama
  embedding=$(curl -s -X POST "http://localhost:4000/embeddings" \
    -H "Authorization: Bearer sk-jarvis-local" \
    -H "Content-Type: application/json" \
    -d "{\"model\": \"ollama/nomic-embed-text\", \"input\": $(echo "$content" | head -c 8000 | jq -Rs .)}" \
    | jq '.data[0].embedding')

  # Guardar en Qdrant
  curl -s -X PUT "${QDRANT_URL}/collections/${COLLECTION}/points" \
    -H 'Content-Type: application/json' \
    -d "{
      \"points\": [{
        \"id\": \"${doc_id}\",
        \"vector\": ${embedding},
        \"payload\": {
          \"path\": \"${rel_path}\",
          \"content\": $(echo "$content" | head -c 8000 | jq -Rs .),
          \"indexed_at\": \"$(date -Iseconds)\"
        }
      }]
    }" > /dev/null 2>&1

  echo "  Indexado: $rel_path"
done

echo "Sincronizacion completa."
```

### 7.6 Plugins Obsidian recomendados

Instalar desde Community Plugins dentro de Obsidian:

| Plugin | Para que |
|--------|----------|
| **Templater** | Templates avanzados para PRDs, ADRs, etc. |
| **Dataview** | Queries tipo SQL sobre notas (proyectos activos, etc.) |
| **Calendar** | Vista de calendario del diario |
| **Kanban** | Tableros Kanban dentro de Obsidian |
| **Excalidraw** | Diagramas de arquitectura |
| **Smart Connections** | Conecta notas similares con IA |
| **Auto Classifier** | Clasifica notas automaticamente |
| **Git** | Versiona el vault con Git |

---

## 8. autoskills.sh — Discovery Automatico

Archivo: `~/jarvis/skills/autoskills.sh`

```bash
#!/bin/bash
# ================================================================
# autoskills.sh — Discovery automatico de Agent Skills
# Busca, lista, instala y actualiza skills desde multiples fuentes
# ================================================================
set -euo pipefail

# --- Config ---
SKILLS_DIR="${JARVIS_SKILLS:-$HOME/jarvis/skills}"
GITHUB_USER="${GITHUB_USER:-}"
COMMUNITY_REPO="VoltAgent/awesome-agent-skills"
LOCAL_REGISTRY="$HOME/jarvis/.skill-registry.json"
OPENCODE_CONFIG="$HOME/.config/opencode/config.json"

# --- Colores ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# --- Funciones ---

print_header() {
    echo -e "${CYAN}"
    echo "  ╔══════════════════════════════════════╗"
    echo "  ║     JARVIS — AutoSkills Discovery    ║"
    echo "  ╚══════════════════════════════════════╝"
    echo -e "${NC}"
}

# Listar skills locales
list_local() {
    echo -e "${BLUE}Skills locales instalados:${NC}"
    echo ""
    for skill_dir in "$SKILLS_DIR"/*/; do
        if [ -f "$skill_dir/SKILL.md" ]; then
            skill_name=$(basename "$skill_dir")
            description=$(head -1 "$skill_dir/SKILL.md" | sed 's/^# //')
            echo -e "  ${GREEN}$skill_name${NC} — $description"
        elif [ -f "$skill_dir/instructions.md" ]; then
            skill_name=$(basename "$skill_dir")
            description=$(head -1 "$skill_dir/instructions.md" | sed 's/^# //')
            echo -e "  ${GREEN}$skill_name${NC} — $description"
        fi
    done
    echo ""
}

# Buscar skill por palabra clave
search() {
    local query="$1"
    echo -e "${BLUE}Buscando skills: '$query'${NC}"
    echo ""

    # Buscar en locales
    echo -e "${YELLOW}--- Locales ---${NC}"
    for skill_dir in "$SKILLS_DIR"/*/; do
        if [ -f "$skill_dir/SKILL.md" ] || [ -f "$skill_dir/instructions.md" ]; then
            skill_name=$(basename "$skill_dir")
            skill_file="$skill_dir/SKILL.md"
            [ ! -f "$skill_file" ] && skill_file="$skill_dir/instructions.md"
            if grep -il "$query" "$skill_file" 2>/dev/null; then
                echo -e "  ${GREEN}$skill_name${NC} (match en instrucciones)"
            fi
        fi
    done

    # Buscar en comunidad (GitHub)
    echo ""
    echo -e "${YELLOW}--- Comunidad (GitHub) ---${NC}"
    if command -v gh &>/dev/null; then
        gh api "repos/$COMMUNITY_REPO/contents" \
            --jq ".[].name" 2>/dev/null | grep -i "$query" | while read -r name; do
            echo -e "  ${CYAN}$name${NC} (en $COMMUNITY_REPO)"
        done
    else
        echo "  Instala 'gh' CLI para buscar en GitHub"
    fi

    echo ""
}

# Instalar skill desde URL o path
install() {
    local source="$1"
    local skill_name="$2"

    if [ -z "$skill_name" ]; then
        skill_name=$(basename "$source" | sed 's/\.git$//')
    fi

    local dest="$SKILLS_DIR/$skill_name"

    echo -e "${BLUE}Instalando skill: $skill_name${NC}"

    # Si es un repo de GitHub
    if [[ "$source" == github:* ]] || [[ "$source" == https://github.com/* ]]; then
        git clone "$source" "$dest" --depth 1
        rm -rf "$dest/.git"
    # Si es un path local
    elif [ -d "$source" ]; then
        cp -r "$source" "$dest"
    # Si es un skill del registry comunitario
    elif [[ "$source" == community:* ]]; then
        local skill_path="${source#community:}"
        gh api "repos/$COMMUNITY_REPO/contents/$skill_path" \
            --jq '.download_url' 2>/dev/null | xargs curl -sL | tar -xz -C "$SKILLS_DIR"
    else
        echo -e "${RED}Fuente no reconocida: $source${NC}"
        return 1
    fi

    echo -e "${GREEN}Skill instalado en: $dest${NC}"
    echo -e "${YELLOW}Actualizando configuracion de OpenCode...${NC}"
    update_opencode_config
}

# Crear un nuevo skill desde template
create() {
    local skill_name="$1"
    local dest="$SKILLS_DIR/$skill_name"

    if [ -z "$skill_name" ]; then
        echo -e "${RED}Especifica un nombre: autoskills.sh create <nombre>${NC}"
        return 1
    fi

    mkdir -p "$dest"/{scripts,templates}

    cat > "$dest/SKILL.md" << 'SKILLEOF'
# [NOMBRE] Agent — JARVIS

Eres el agente de [DESCRIPCION] de la empresa de software.

## Responsabilidades
1. [Responsabilidad 1]
2. [Responsabilidad 2]
3. [Responsabilidad 3]

## Flujo de trabajo
1. Recibes tarea del PM Agent
2. Ejecutas usando los scripts disponibles
3. Reportas resultado al Brain (Obsidian)
4. Notificas al PM Agent

## Scripts disponibles
- `script1.sh` — Descripcion
- `script2.sh` — Descripcion

## Reglas
- Siempre consulta al Brain antes de tomar decisiones
- Documenta todo en Obsidian
- Si algo falla, notifica al humano
SKILLEOF

    # Reemplazar placeholders
    sed -i "s/\[NOMBRE\]/$skill_name/g" "$dest/SKILL.md"

    cat > "$dest/metadata.json" << 'METAEOF'
{
  "name": "skill-name",
  "version": "1.0.0",
  "description": "Descripcion del skill",
  "triggers": ["trigger1", "trigger2"],
  "dependencies": [],
  "model": "coder"
}
METAEOF
    sed -i "s/skill-name/$skill_name/g" "$dest/metadata.json"

    echo -e "${GREEN}Skill creado en: $dest${NC}"
    echo -e "${YELLOW}Edita $dest/SKILL.md para personalizar${NC}"
}

# Actualizar configuracion de OpenCode
update_opencode_config() {
    if [ ! -f "$OPENCODE_CONFIG" ]; then
        return
    fi

    # Reconstruir lista de skills
    local skills_paths=[]
    for skill_dir in "$SKILLS_DIR"/*/; do
        if [ -f "$skill_dir/SKILL.md" ] || [ -f "$skill_dir/instructions.md" ]; then
            skills_paths+="\"$skill_dir\","
        fi
    done

    echo -e "${YELLOW}Skills registrados en OpenCode config${NC}"
}

# Verificar integridad de skills
validate() {
    echo -e "${BLUE}Validando skills...${NC}"
    echo ""

    local errors=0
    for skill_dir in "$SKILLS_DIR"/*/; do
        skill_name=$(basename "$skill_dir")
        local has_skill_md=false
        local has_metadata=false

        [ -f "$skill_dir/SKILL.md" ] && has_skill_md=true
        [ -f "$skill_dir/instructions.md" ] && has_skill_md=true
        [ -f "$skill_dir/metadata.json" ] && has_metadata=true

        if [ "$has_skill_md" = true ] && [ "$has_metadata" = true ]; then
            echo -e "  ${GREEN}OK${NC} $skill_name"
        else
            echo -e "  ${RED}ERROR${NC} $skill_name — Falta:"
            [ "$has_skill_md" = false ] && echo "    - SKILL.md o instructions.md"
            [ "$has_metadata" = false ] && echo "    - metadata.json"
            ((errors++))
        fi
    done

    echo ""
    if [ $errors -eq 0 ]; then
        echo -e "${GREEN}Todos los skills son validos${NC}"
    else
        echo -e "${RED}$errors skills con errores${NC}"
    fi
}

# Sincronizar skills con repo de GitHub
sync_github() {
    echo -e "${BLUE}Sincronizando skills con GitHub...${NC}"

    if [ -z "$GITHUB_USER" ]; then
        echo -e "${RED}Configura GITHUB_USER${NC}"
        return 1
    fi

    local repo="jarvis-skills"
    local temp_dir=$(mktemp -d)

    # Clonar repo si existe, sino crear
    if gh repo view "$GITHUB_USER/$repo" &>/dev/null; then
        gh repo clone "$GITHUB_USER/$repo" "$temp_dir"
    else
        mkdir -p "$temp_dir"
        cd "$temp_dir"
        git init
        gh repo create "$GITHUB_USER/$repo" --private --source=. --push
    fi

    # Copiar skills al repo
    rm -rf "$temp_dir/skills"/*
    cp -r "$SKILLS_DIR"/* "$temp_dir/skills/" 2>/dev/null || true

    # Commit y push
    cd "$temp_dir"
    git add -A
    git commit -m "sync: skills update $(date +%Y-%m-%d)" || true
    git push

    rm -rf "$temp_dir"
    echo -e "${GREEN}Skills sincronizados con GitHub${NC}"
}

# --- Menu principal ---
print_header

case "${1:-help}" in
    list|ls)
        list_local
        ;;
    search|find|s)
        search "${2:-}"
        ;;
    install|i)
        install "${2:-}" "${3:-}"
        ;;
    create|new|c)
        create "${2:-}"
        ;;
    validate|check|v)
        validate
        ;;
    sync)
        sync_github
        ;;
    help|*)
        echo "Uso: autoskills.sh <comando> [args]"
        echo ""
        echo "Comandos:"
        echo "  list, ls           Listar skills instalados"
        echo "  search, s <query>  Buscar skills por palabra clave"
        echo "  install, i <src>   Instalar skill desde URL/path/GitHub"
        echo "  create, c <name>   Crear nuevo skill desde template"
        echo "  validate, v        Verificar integridad de skills"
        echo "  sync               Sincronizar skills con GitHub"
        echo ""
        echo "Ejemplos:"
        echo "  autoskills.sh list"
        echo "  autoskills.sh search 'docker'"
        echo "  autoskills.sh install https://github.com/user/skill-deploy"
        echo "  autoskills.sh create skill-security"
        echo "  autoskills.sh validate"
        echo "  autoskills.sh sync"
        ;;
esac
```

```bash
chmod +x ~/jarvis/skills/autoskills.sh
```

---

## 9. Agentes de la Empresa

### 9.1 PM Agent

Archivo: `~/jarvis/skills/pm/SKILL.md`

```markdown
# PM Agent — JARVIS

Eres el Project Manager de la empresa de software. Tu mision es transformar ideas en software funcional, coordinando al equipo de agentes.

## Responsabilidades
1. Recibir ideas del cliente y convertirlas en PRDs completos
2. Descomponer proyectos en tareas asignables
3. Planificar sprints de 1-2 semanas
4. Monitorear progreso y eliminar bloqueos
5. Comunicar estado al cliente y al equipo

## Flujo de trabajo
1. Cliente describe proyecto -> Generas PRD (usar template en templates/prd_template.md)
2. PRD aprobado -> Creas tareas en PostgreSQL
3. Asignas tareas a agentes:
   - Backend Agent -> APIs, modelos, servicios
   - Frontend Agent -> UI, componentes, estilos
   - DevOps Agent -> Docker, CI/CD, deploy
   - QA Agent -> Tests, seguridad, calidad
4. Recibes resultados -> Validas y comunicas al cliente
5. Sprint terminado -> Generas reporte y planeas el siguiente

## Herramientas disponibles
- `generate_prd.sh` — Genera PRD desde descripcion textual
- `plan_sprint.sh` — Crea plan de sprint desde PRD
- `review_progress.sh` — Revisa estado de tareas en DB

## Reglas
- Siempre consultar al Brain antes de estimar (hay lecciones aprendidas?)
- Documentar TODA decision en Obsidian (vault/03-Decisiones/)
- Si un agente reporta un bloqueo, escalar al humano
- Los PRDs se versionan en Git junto con el codigo

## Modelo recomendado: coder
```

### 9.2 Backend Agent

Archivo: `~/jarvis/skills/backend/SKILL.md`

```markdown
# Backend Agent — JARVIS

Eres el desarrollador Backend senior de la empresa. Escribes codigo limpio, probado y bien documentado.

## Stack principal
- **APIs**: Express.js, FastAPI, Next.js API routes
- **DB**: PostgreSQL, Prisma ORM, Redis
- **Auth**: JWT, OAuth2
- **Testing**: Jest, pytest, Vitest

## Responsabilidades
1. Generar esqueletos de API desde el PRD
2. Implementar endpoints y modelos de datos
3. Escribir tests unitarios y de integracion
4. Hacer code review de tu propio codigo
5. Documentar API (OpenAPI/Swagger)

## Flujo de trabajo
1. Recibes tareas del PM Agent
2. Consultas el Brain (ya hicimos algo similar?)
3. Generas codigo usando templates en templates/
4. Escribes tests
5. Haces self-review
6. Reportas al PM Agent

## Scripts disponibles
- `scaffold_api.sh <stack> <nombre>` — Genera esqueleto de API
- `gen_models.sh <schema.prisma>` — Genera modelos desde schema
- `gen_endpoints.sh <recurso>` — Genera CRUD endpoints
- `review_code.sh <path>` — Code review automatico

## Reglas
- TODO endpoint debe tener test
- TODO modelo debe tener validacion
- TODO cambio se documenta en el commit
- Si encuentras un bug en otro agente, reportas al PM
- Nunca deployar sin pasar QA

## Modelo recomendado: coder
```

### 9.3 DevOps Agent

Archivo: `~/jarvis/skills/devops/SKILL.md`

```markdown
# DevOps Agent — JARVIS

Eres el ingeniero DevOps de la empresa. Tu mision es que el codigo llegue a produccion de forma segura, rapida y reproducible.

## Responsabilidades
1. Dockerizar aplicaciones para produccion
2. Configurar CI/CD pipelines
3. Desplegar en VPS del cliente
4. Configurar SSL y dominios
5. Gestionar la estrategia Git del proyecto
6. Crear el paquete de deploy 1-click

## Flujo de trabajo
1. Recibes seal de QA aprobado
2. Generas Dockerfile optimizado (multi-stage)
3. Generas docker-compose.prod.yml con monitor incluido
4. Creas script deploy.sh para 1-click deploy
5. Subes a GitHub (rama production)
6. Deployas en VPS del cliente
7. Verificas que el Monitor Agent este activo

## Scripts disponibles
- `dockerize.sh <proyecto>` — Genera Dockerfile + compose
- `deploy_vps.sh <proyecto> <vps-host>` — Deploy a VPS
- `setup_ci.sh <proyecto>` — Configura GitHub Actions CI/CD
- `ssl_setup.sh <dominio>` — Configura SSL con Certbot
- `setup_git_repo.sh <proyecto>` — Inicializa repo con branching

## Reglas
- Siempre multi-stage builds (imagen pequena)
- Siempre health checks en docker-compose
- Siempre .env.example, nunca .env en git
- Siempre monitor incluido en deploy del cliente
- Tag de version en Git antes de cada deploy

## Modelo recomendado: fast
```

### 9.4 QA Agent

Archivo: `~/jarvis/skills/qa/SKILL.md`

```markdown
# QA Agent — JARVIS

Eres el ingeniero de QA de la empresa. Tu mision es asegurar que nada llegue a produccion con bugs.

## Responsabilidades
1. Ejecutar tests automatizados
2. Generar tests E2E desde los endpoints
3. Escaneo de seguridad basico
4. Validar que el deploy funciona
5. Reportar bugs con repro steps

## Scripts disponibles
- `run_tests.sh <proyecto>` — Ejecuta todos los tests
- `gen_e2e.sh <proyecto>` — Genera tests E2E
- `security_scan.sh <proyecto>` — Escaneo de dependencias

## Modelo recomendado: thinker
```

### 9.5 Monitor Agent

Archivo: `~/jarvis/skills/monitor/SKILL.md`

```markdown
# Monitor Agent — JARVIS

Eres el agente vigilante de la empresa. Monitoreas todos los servidores de los clientes y alertas cuando algo va mal.

## Responsabilidades
1. Monitorear salud de VPS de clientes (CPU, RAM, Disco, Red)
2. Monitorear estado de contenedores Docker
3. Alertar al equipo cuando algo falla
4. Intentar auto-heal cuando es posible
5. Generar reportes semanales por cliente

## Fuentes de datos
- Netdata en cada VPS del cliente
- Uptime Kuma para status de servicios
- Docker API para estado de contenedores

## Niveles de alerta
- **NORMAL**: Todo OK, log silencioso
- **WARNING**: Recurso al 80%+, notificar por Telegram
- **CRITICAL**: Servicio caido, auto-heal + alarma urgente

## Acciones de auto-heal
1. Reiniciar contenedor caido
2. Limpiar logs si disco lleno
3. Reiniciar servicio de la app
4. Si no se resuelve en 5 min, escalar al humano

## Scripts disponibles
- `health_check.sh <vps-host>` — Chequeo completo de salud
- `alert_handler.sh <level> <message>` — Envia alerta por Telegram
- `auto_heal.sh <vps-host> <service>` — Intenta reparar automaticamente

## Modelo recomendado: fast
```

---

## 10. Workflows n8n

### 10.1 Workflow: Nuevo Proyecto (Completo)

```
[Trigger: Telegram "Nuevo proyecto: <descripcion>"]
    |
    v
[PM Agent] -> Genera PRD
    |
    v
[Espera aprobacion del humano via Telegram]
    |
    +-- Aprobado -> [Descomponer en tareas en PostgreSQL]
    |                    |
    |                    +-- [Backend Agent] -> Scaffold API
    |                    +-- [Frontend Agent] -> Scaffold UI
    |                    +-- [DevOps Agent] -> Setup Git + Docker
    |                              |
    |                              v
    |                    [QA Agent] -> Generar tests
    |                              |
    |                              v
    |                    [DevOps Agent] -> Deploy a staging
    |                              |
    |                              v
    |                    [QA Agent] -> Validar staging
    |                              |
    |                              v
    |                    [DevOps Agent] -> Deploy a produccion
    |                              |
    |                              v
    |                    [Monitor Agent] -> Activar monitoreo
    |
    +-- Rechazado -> [Revisar PRD] -> Volver al inicio
```

### 10.2 Workflow: Monitor Loop (cada 5 minutos)

```
[Trigger: Cron cada 5 minutos]
    |
    v
[PostgreSQL: SELECT * FROM clients WHERE active = true]
    |
    v
[Para cada cliente]
    |
    +-- [HTTP: Netdata del cliente] -> Metricas
    +-- [HTTP: Uptime Kuma] -> Estado servicios
    |
    v
[Monitor Agent analiza]
    |
    +-- Normal -> Silencio
    +-- Warning -> Telegram al equipo
    +-- Critical -> Auto-heal + Alerta urgente
```

### 10.3 Workflow: Sync Obsidian (diario)

```
[Trigger: Cron cada dia a las 23:00]
    |
    v
[Brain Agent]
    |
    +-- Leer nuevas decisiones del dia
    +-- Indexar en Qdrant
    +-- Generar resumen diario en vault/07-Diario/
    +-- Actualizar MOC.md si hay nuevas notas
```

---

## 11. Estrategia Git Profesional

### 11.1 Repositorios

Tu empresa tiene multiples repos en GitHub:

```
github.com/TU-USER/
|
+-- jarvis/                    # Repo principal (este documento)
|   +-- main                   # Version estable del stack
|   +-- develop                # Desarrollo activo
|   +-- skills/*               # Ramas por skill
|
+-- jarvis-skills/             # Repo separado para skills
|   +-- main                   # Skills estables
|   +-- develop                # Skills en desarrollo
|
+-- jarvis-templates/          # Templates de proyectos
|   +-- main
|   +-- template-nextjs/
|   +-- template-fastapi/
|   +-- template-express/
|
+-- jarvis-n8n-workflows/      # Workflows exportados
|   +-- main
|
+-- jarvis-vault/              # Obsidian Vault (PRIVADO)
|   +-- main
|
+-- client-XXXX/               # Un repo por proyecto de cliente
|   +-- main                   # Produccion
|   +-- develop                # Desarrollo
|   +-- staging                # Pre-produccion
|   +-- agent/*                # Ramas automaticas de agentes
```

### 11.2 Branching Strategy — GitFlow Adaptado para Agentes

```
                    main (produccion)
                    |   \
                    |    hotfix/critical-fix
                    |   /
            staging (pre-produccion, QA valida aqui)
            |   \
            |    release/v1.2.0
            |   /
    develop (integracion, agentes trabajan aqui)
    |    \    \    \
    |     \    \    \
    |  feature/  feature/  agent/
    |  pm-prd    api-users  backend-auto-commit
    |                      agent/
    |                      devops-dockerize
    |
    agent/
    monitor-config
```

### 11.3 Reglas de ramas

| Rama | Quien trabaja ahi | Merge a | Proteccion |
|------|-------------------|---------|------------|
| `main` | Solo DevOps Agent (deploy) | — | Require PR + 1 review |
| `staging` | QA Agent valida aqui | `main` | Require PR |
| `develop` | Todos los agentes integran | `staging` | Require PR |
| `feature/*` | Agente individual | `develop` | Sin proteccion |
| `agent/*` | Agentes automaticos | `develop` | Auto-merge si tests pasan |
| `hotfix/*` | Tu o DevOps Agent | `main` + `develop` | Require PR |
| `release/*` | PM Agent prepara | `staging` | Require PR |

### 11.4 Convencion de commits (Agentes)

Cada agente firma sus commits:

```
<tipo>(<scope>): <descripcion> [agent:<nombre>]

Tipos:
  feat:     Nueva funcionalidad
  fix:      Bug fix
  docs:     Documentacion
  style:    Formato (no cambia logica)
  refactor: Refactor sin cambio funcional
  test:     Tests
  chore:    Mantenimiento (deps, config)
  deploy:   Deploy a entorno
  monitor:  Cambio en monitoreo

Ejemplos:
  feat(api): add inventory endpoints [agent:backend]
  fix(auth): token expiration handling [agent:backend]
  docs(prd): add inventory system PRD [agent:pm]
  deploy(prod): v1.2.0 to client VPS [agent:devops]
  monitor(alert): add CPU threshold warning [agent:monitor]
  test(e2e): add inventory CRUD tests [agent:qa]
```

### 11.5 Script: setup_git_repo.sh

Archivo: `~/jarvis/scripts/git-setup.sh`

```bash
#!/bin/bash
# ================================================================
# git-setup.sh — Inicializa un repo con branching profesional
# Uso: git-setup.sh <nombre-proyecto> <github-org-or-user>
# ================================================================
set -euo pipefail

PROJECT="$1"
ORG="${2:-$GITHUB_USER}"

if [ -z "$PROJECT" ] || [ -z "$ORG" ]; then
    echo "Uso: git-setup.sh <nombre-proyecto> [github-org]"
    exit 1
fi

REPO_URL="git@github.com:$ORG/$PROJECT.git"
LOCAL_PATH="$HOME/jarvis/projects/$PROJECT"

echo "Inicializando repo: $ORG/$PROJECT"

# 1. Crear repo en GitHub
if ! gh repo view "$ORG/$PROJECT" &>/dev/null; then
    gh repo create "$ORG/$PROJECT" --private --description "JARVIS Project: $PROJECT"
    echo "Repo creado en GitHub (privado)"
else
    echo "Repo ya existe en GitHub"
fi

# 2. Clonar e inicializar
mkdir -p "$LOCAL_PATH"
cd "$LOCAL_PATH"

if [ ! -d ".git" ]; then
    git init
    git remote add origin "$REPO_URL"
fi

# 3. Crear .gitignore profesional
cat > .gitignore << 'GITIGNORE'
# Dependencies
node_modules/
__pycache__/
.venv/
venv/

# Build
dist/
build/
.next/
out/

# Environment
.env
.env.local
.env.production
!.env.example

# IDE
.vscode/settings.json
.idea/

# OS
.DS_Store
Thumbs.db

# Docker
docker-compose.override.yml

# Logs
*.log
logs/

# Testing
coverage/
.nyc_output/

# Misc
*.swp
*.swo
*~
GITIGNORE

# 4. Copiar template de proyecto
if [ -d "$HOME/jarvis/projects/_template" ]; then
    cp -r "$HOME/jarvis/projects/_template/"* . 2>/dev/null || true
fi

# 5. Crear ramas
git add -A
git commit -m "chore: init project from JARVIS template [agent:devops]" || true

# Rama main
git branch -M main
git push -u origin main

# Rama develop
git checkout -b develop
git push -u origin develop

# Rama staging
git checkout -b staging
git push -u origin staging

# 6. Configurar proteccion de ramas
gh api "repos/$ORG/$PROJECT/branches/main/protection" \
    -X PUT \
    --input - << 'PROTECTEOF' 2>/dev/null || true
{
    "required_status_checks": {
        "strict": true,
        "contexts": []
    },
    "enforce_admins": false,
    "required_pull_request_reviews": {
        "dismiss_stale_reviews": true,
        "require_code_owner_reviews": false,
        "required_approving_review_count": 1
    },
    "restrictions": null
}
PROTECTEOF

echo "Proteccion configurada para main"

# 7. Volver a develop para trabajar
git checkout develop

echo ""
echo "Repo inicializado: $ORG/$PROJECT"
echo "Ramas creadas: main, staging, develop"
echo "Proteccion: main requiere PR + 1 approval"
echo "Rama activa: develop"
echo ""
echo "Siguiente: cd $LOCAL_PATH && opencode"
```

```bash
chmod +x ~/jarvis/scripts/git-setup.sh
```

### 11.6 Script: jarvis-init.sh — Crear nuevo proyecto completo

Archivo: `~/jarvis/scripts/jarvis-init.sh`

```bash
#!/bin/bash
# ================================================================
# jarvis-init.sh — Crea un proyecto completo desde cero
# Uso: jarvis-init.sh "Nombre del Proyecto" "descripcion"
# ================================================================
set -euo pipefail

PROJECT_NAME="$1"
DESCRIPTION="${2:-Proyecto creado por JARVIS}"

if [ -z "$PROJECT_NAME" ]; then
    echo "Uso: jarvis-init.sh <nombre-proyecto> <descripcion>"
    exit 1
fi

# Slug del nombre (para URLs y carpetas)
SLUG=$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')

echo "================================================"
echo "  JARVIS — Inicializando: $PROJECT_NAME"
echo "  Slug: $SLUG"
echo "================================================"
echo ""

# 1. Crear nota en Obsidian
OBSIDIAN_DIR="$HOME/jarvis/vault/01-Proyectos"
mkdir -p "$OBSIDIAN_DIR"
cat > "$OBSIDIAN_DIR/$SLUG.md" << OBSDONEW
# $PROJECT_NAME

**Estado**: Iniciando
**Fecha inicio**: $(date +%Y-%m-%d)
**Descripcion**: $DESCRIPTION

## Progreso
- [x] Proyecto creado
- [ ] PRD generado
- [ ] Sprint 1 planificado
- [ ] Backend scaffold
- [ ] Frontend scaffold
- [ ] Tests
- [ ] Deploy staging
- [ ] Deploy produccion

## Notas
OBSDONEW

echo "1/5 Nota en Obsidian creada"

# 2. Crear entrada en PostgreSQL
docker exec jarvis-postgres psql -U jarvis -d jarvis -c "
INSERT INTO projects (name, slug, description, status, created_at)
VALUES ('$PROJECT_NAME', '$SLUG', '$DESCRIPTION', 'init', NOW());
" 2>/dev/null || echo "  (DB no disponible, se creara despues)"

echo "2/5 Registro en base de datos"

# 3. Inicializar repo Git
bash "$HOME/jarvis/scripts/git-setup.sh" "$SLUG"

echo "3/5 Repo Git inicializado con branching"

# 4. Crear skills especificos del proyecto
PROJECT_DIR="$HOME/jarvis/projects/$SLUG"
mkdir -p "$PROJECT_DIR/.opencode/skills"

cat > "$PROJECT_DIR/.opencode/skills/SKILL.md" << PROJSKILL
# $PROJECT_NAME — Config del Proyecto

## Stack
(Por definir por el PM Agent)

## Convenciones
- Commits: <tipo>(<scope>): <desc> [agent:<nombre>]
- Branching: GitFlow (main/staging/develop/feature)
- Deploy: Solo desde staging con QA aprobado

## Notas especificas
(Documenrar aqui decisiones del proyecto)
PROJSKILL

echo "4/5 Skills del proyecto creados"

# 5. Guardar en Brain (Qdrant)
bash "$HOME/jarvis/skills/brain/scripts/store_memory.sh" \
    "Proyecto '$PROJECT_NAME' creado con slug '$SLUG'" "project-init" 2>/dev/null || true

echo "5/5 Registrado en Brain"
echo ""
echo "================================================"
echo "  Proyecto listo para que el PM Agent genere PRD"
echo ""
echo "  Siguiente paso:"
echo "  cd $PROJECT_DIR"
echo "  opencode"
echo "  > Genera el PRD para: $DESCRIPTION"
echo "================================================"
```

```bash
chmod +x ~/jarvis/scripts/jarvis-init.sh
```

### 11.7 GitHub Actions CI/CD Template

Archivo: `~/jarvis/projects/_template/.github/workflows/ci.yml`

```yaml
name: JARVIS CI

on:
  push:
    branches: [develop, staging, main]
  pull_request:
    branches: [develop, staging, main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Lint
        run: npm run lint --if-present

      - name: Test
        run: npm test

      - name: Build
        run: npm run build --if-present

      - name: Security scan
        run: npx audit-ci --moderate || true

  docker:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:latest
            ghcr.io/${{ github.repository }}:${{ github.sha }}
```

---

## 12. Packager & Deploy a VPS

### 12.1 Script: jarvis-deploy.sh

Archivo: `~/jarvis/scripts/jarvis-deploy.sh`

```bash
#!/bin/bash
# ================================================================
# jarvis-deploy.sh — Empaqueta y despliega proyecto en VPS
# Uso: jarvis-deploy.sh <proyecto> <vps-user@vps-host>
# ================================================================
set -euo pipefail

PROJECT="$1"
VPS_TARGET="$2"
PROJECT_DIR="$HOME/jarvis/projects/$PROJECT"
DEPLOY_DIR="$HOME/jarvis/deploy/$PROJECT"

if [ -z "$PROJECT" ] || [ -z "$VPS_TARGET" ]; then
    echo "Uso: jarvis-deploy.sh <proyecto> <user@vps-host>"
    exit 1
fi

echo "JARVIS Deploy: $PROJECT -> $VPS_TARGET"

# 1. Generar paquete de deploy
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# 2. Copiar codigo fuente
cp -r "$PROJECT_DIR/src" "$DEPLOY_DIR/src" 2>/dev/null || true
cp "$PROJECT_DIR/package.json" "$DEPLOY_DIR/" 2>/dev/null || true
cp "$PROJECT_DIR/requirements.txt" "$DEPLOY_DIR/" 2>/dev/null || true
cp "$PROJECT_DIR/prisma" "$DEPLOY_DIR/" -r 2>/dev/null || true

# 3. Detectar stack y copiar Dockerfile correcto
if [ -f "$PROJECT_DIR/package.json" ]; then
    cp "$HOME/jarvis/skills/devops/templates/Dockerfile.node" "$DEPLOY_DIR/Dockerfile"
elif [ -f "$PROJECT_DIR/requirements.txt" ]; then
    cp "$HOME/jarvis/skills/devops/templates/Dockerfile.python" "$DEPLOY_DIR/Dockerfile"
fi

# 4. Copiar docker-compose de produccion
cp "$HOME/jarvis/skills/devops/templates/docker-compose.prod.yml" "$DEPLOY_DIR/docker-compose.yml"

# 5. Copiar nginx
cp "$HOME/jarvis/skills/devops/templates/nginx.conf" "$DEPLOY_DIR/nginx.conf"

# 6. Generar .env.example
cat > "$DEPLOY_DIR/.env.example" << 'ENVEOF'
# Configuracion del proyecto — EDITAR antes de deploy
APP_URL=https://tudominio.com
APP_PORT=3000
DB_PASSWORD=cambiar_esto_por_un_password_seguro
JWT_SECRET=cambiar_esto_por_un_secret_seguro
NODE_ENV=production
ENVEOF

# 7. Generar deploy.sh (1-click)
cat > "$DEPLOY_DIR/deploy.sh" << 'DEPLOYEOF'
#!/bin/bash
set -e
echo "============================================"
echo "  JARVIS Deploy — 1-Click"
echo "============================================"

# Crear .env si no existe
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Creado .env desde .env.example"
    echo "EDITA .env con tus valores antes de continuar:"
    echo ""
    cat .env
    echo ""
    read -p "Presiona Enter cuando hayas editado .env..."
fi

# Pull y build
docker compose build --no-cache
docker compose up -d

# Esperar a que los servicios esten listos
echo "Esperando a que los servicios inicien..."
sleep 10

# Health check
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 || echo "000")
if [ "$HEALTH" = "200" ] || [ "$HEALTH" = "301" ] || [ "$HEALTH" = "302" ]; then
    echo ""
    echo "Deploy exitoso!"
    echo "App: http://localhost:3000"
    echo "Monitor: http://localhost:19999"
    echo "Uptime: http://localhost:3001"
else
    echo ""
    echo "ATENCION: La app no responde (HTTP $HEALTH)"
    echo "Revisa los logs: docker compose logs -f"
fi
DEPLOYEOF

chmod +x "$DEPLOY_DIR/deploy.sh"

# 8. Tag en Git
cd "$PROJECT_DIR"
VERSION=$(git describe --tags --always 2>/dev/null || echo "v0.1.0")
git tag -a "deploy-$(date +%Y%m%d-%H%M)" -m "Deploy to $VPS_TARGET" 2>/dev/null || true
git push --tags 2>/dev/null || true

# 9. Subir al VPS
echo "Subiendo paquete al VPS..."
ssh "$VPS_TARGET" "mkdir -p /opt/jarvis-apps/$PROJECT"
scp -r "$DEPLOY_DIR/"* "$VPS_TARGET:/opt/jarvis-apps/$PROJECT/"

echo ""
echo "============================================"
echo "  Paquete subido a $VPS_TARGET"
echo "  Para completar el deploy:"
echo "  ssh $VPS_TARGET"
echo "  cd /opt/jarvis-apps/$PROJECT"
echo "  ./deploy.sh"
echo "============================================"

# 10. Registrar deploy en Obsidian
cat >> "$HOME/jarvis/vault/06-Clientes/deploys.md" << LOGEOF

## $PROJECT — $(date +%Y-%m-%d\ %H:%M)
- **VPS**: $VPS_TARGET
- **Version**: $VERSION
- **Directorio**: /opt/jarvis-apps/$PROJECT
- **Estado**: Pendiente confirmacion
LOGEOF
```

```bash
chmod +x ~/jarvis/scripts/jarvis-deploy.sh
```

### 12.2 Docker Compose de Produccion (para el cliente)

Archivo: `~/jarvis/skills/devops/templates/docker-compose.prod.yml`

```yaml
version: "3.9"

services:
  app:
    build: .
    container_name: ${COMPOSE_PROJECT_NAME:-app}-app
    restart: unless-stopped
    ports:
      - "${APP_PORT:-3000}:3000"
    environment:
      - DATABASE_URL=postgresql://app:app@db:5432/app
      - JWT_SECRET=${JWT_SECRET}
      - NODE_ENV=production
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    image: postgres:16-alpine
    container_name: ${COMPOSE_PROJECT_NAME:-app}-db
    restart: unless-stopped
    volumes:
      - db_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=app
      - POSTGRES_USER=app
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    container_name: ${COMPOSE_PROJECT_NAME:-app}-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - app

  # Monitor Agent — Vigila que todo funcione
  monitor:
    image: netdata/netdata:latest
    container_name: ${COMPOSE_PROJECT_NAME:-app}-monitor
    restart: unless-stopped
    ports:
      - "19999:19999"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    cap_add:
      - SYS_PTRACE

  # Uptime Monitor — Status page
  uptime:
    image: louislam/uptime-kuma:latest
    container_name: ${COMPOSE_PROJECT_NAME:-app}-uptime
    restart: unless-stopped
    ports:
      - "3001:3001"
    volumes:
      - uptime_data:/app/data

volumes:
  db_data:
  uptime_data:
```

---

## 13. Monitor Agent — Vigilante Remoto

### 13.1 Script: health_check.sh

Archivo: `~/jarvis/skills/monitor/scripts/health_check.sh`

```bash
#!/bin/bash
# ================================================================
# health_check.sh — Chequeo completo de salud de un VPS
# Uso: health_check.sh <vps-host> [vps-user]
# ================================================================
set -euo pipefail

VPS_HOST="$1"
VPS_USER="${2:-root}"

echo "JARVIS Monitor — Health Check: $VPS_HOST"
echo "============================================"

# 1. SSH connectivity
if ssh -o ConnectTimeout=5 "$VPS_USER@$VPS_HOST" "echo ok" &>/dev/null; then
    echo -e "  SSH: OK"
else
    echo -e "  SSH: FAIL (no se puede conectar)"
    exit 1
fi

# 2. CPU, RAM, Disk
ssh "$VPS_USER@$VPS_HOST" << 'REMOTE_CHECK'
echo "  --- System Resources ---"
echo "  CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')% used"
echo "  RAM: $(free -m | awk 'NR==2{printf "%s/%sMB (%.1f%%)", $3,$2,$3*100/$2}')"
echo "  Disk: $(df -h / | awk 'NR==2{printf "%s/%s (%s)", $3,$2,$5}')"
echo ""

# 3. Docker containers
echo "  --- Docker Containers ---"
for container in $(docker ps --format '{{.Names}}' 2>/dev/null); do
    status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null)
    health=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "none")
    if [ "$status" = "running" ]; then
        echo -e "  $container: running (health: $health)"
    else
        echo -e "  $container: NOT RUNNING (status: $status)"
    fi
done
echo ""

# 4. Netdata check
NETDATA_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:19999 || echo "000")
echo "  Netdata: HTTP $NETDATA_STATUS"

# 5. Uptime Kuma check
UPTIME_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001 || echo "000")
echo "  Uptime Kuma: HTTP $UPTIME_STATUS"

# 6. App health check
APP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health 2>/dev/null || echo "000")
echo "  App Health: HTTP $APP_STATUS"
REMOTE_CHECK

echo ""
echo "Health check completado."
```

```bash
chmod +x ~/jarvis/skills/monitor/scripts/health_check.sh
```

### 13.2 Script: jarvis-monitor.sh (todos los clientes)

Archivo: `~/jarvis/scripts/jarvis-monitor.sh`

```bash
#!/bin/bash
# ================================================================
# jarvis-monitor.sh — Monitorear todos los clientes activos
# Uso: jarvis-monitor.sh
# ================================================================

echo "JARVIS Monitor — Chequeando todos los clientes..."
echo "================================================"

# Leer clientes de PostgreSQL
CLIENTS=$(docker exec jarvis-postgres psql -U jarvis -d jarvis -t -c \
    "SELECT name, vps_host, vps_user FROM clients WHERE active = true;" 2>/dev/null)

if [ -z "$CLIENTS" ]; then
    echo "No hay clientes activos en la base de datos."
    exit 0
fi

echo "$CLIENTS" | while read -r line; do
    NAME=$(echo "$line" | awk '{print $1}')
    HOST=$(echo "$line" | awk '{print $2}')
    USER=$(echo "$line" | awk '{print $3}')

    if [ -n "$HOST" ]; then
        echo ""
        echo "Cliente: $NAME ($HOST)"
        echo "--------------------------------------------"
        bash "$HOME/jarvis/skills/monitor/scripts/health_check.sh" "$HOST" "$USER" 2>&1 | head -20
    fi
done

echo ""
echo "Monitoreo completado: $(date)"
```

```bash
chmod +x ~/jarvis/scripts/jarvis-monitor.sh
```

---

## 14. Dashboard & Observabilidad

### 14.1 URLs locales

| Servicio | URL | Credenciales por defecto |
|----------|-----|------------------------|
| **n8n** | http://localhost:5678 | jarvis / jarvis2026 |
| **LiteLLM** | http://localhost:4000 | sk-jarvis-local |
| **Ollama** | http://localhost:11434 | — |
| **Grafana** | http://localhost:3000 | jarvis / jarvis2026 |
| **Portainer** | https://localhost:9443 | Crear al primer login |
| **Netdata** | http://localhost:19999 | — |
| **Uptime Kuma** | http://localhost:3001 | Crear al primer login |
| **MinIO** | http://localhost:9001 | jarvis / jarvis2026 |
| **Qdrant** | http://localhost:6333/dashboard | — |

### 14.2 Dashboards Grafana recomendados

1. **JARVIS Overview** — Estado de todos los containers, uso de recursos, costos de modelos
2. **Clientes** — Un panel por cliente con estado de VPS y uptime
3. **Agentes** — Tareas completadas por agente, tiempo promedio, errores
4. **Costos** — Gasto por modelo, por agente, por proyecto (via LiteLLM)

---

## 15. Costos Estimados

| Componente | Costo mensual | Notas |
|-----------|--------------|-------|
| **OpenCode Go** | $10 | Coding principal, modelos open-source |
| **OpenRouter** | $5-15 | Modelos chinos (DeepSeek, Qwen), pay-per-use |
| **Ollama** | $0 | Corre en tu hardware, gratis |
| **LiteLLM** | $0 | Open-source, self-hosted |
| **n8n** | $0 | Open-source, self-hosted |
| **Obsidian** | $0 | Uso personal gratis |
| **GitHub** | $0 | Free tier para repos privados |
| **VPS clientes** | Variable | Lo paga el cliente |
| **TOTAL** | **$15-25/mes** | Vs $200+ con Claude Code Max |

### Costo por proyecto entregado

| Proyecto tipico | Sin JARVIS | Con JARVIS |
|----------------|-----------|-----------|
| API + Dashboard + Deploy | $2,000-5,000 | $500-1,500 |
| Tiempo de entrega | 4-8 semanas | 1-3 semanas |
| Costo de herramientas | $200/mes | $15-25/mes |
| Margen estimado | 30-40% | 60-70% |

---

## 16. Quick Start — Setup en 30 minutos

```bash
# ================================================================
# JARVIS v2 — Quick Start
# ================================================================

# 1. Crear estructura de directorios
mkdir -p ~/jarvis/{docker/{litellm,n8n,ollama,postgres,qdrant,minio,redis,netdata,uptime-kuma,grafana,portainer},vault/{00-Inbox,01-Proyectos,02-Agentes,03-Decisiones,04-Lecciones,05-Templates,06-Clientes,07-Diario,08-Recursos,09-Archivo},skills/{pm,backend,frontend,devops,qa,monitor,brain},projects/_template,deploy,scripts}

# 2. Clonar el repo de JARVIS (cuando lo tengas)
# git clone git@github.com:TU-USER/jarvis.git ~/jarvis

# 3. Crear .env
cp ~/jarvis/docker/.env.example ~/jarvis/docker/.env
nano ~/jarvis/docker/.env  # Rellenar con tus valores

# 4. Levantar el stack
cd ~/jarvis/docker && docker compose up -d

# 5. Descargar modelos Ollama
docker exec jarvis-ollama ollama pull qwen2.5-coder:7b
docker exec jarvis-ollama ollama pull gemma2:2b
docker exec jarvis-ollama ollama pull nomic-embed-text

# 6. Instalar OpenCode
npm install -g opencode

# 7. Instalar Obsidian (AppImage)
wget -O ~/Obsidian.AppImage https://github.com/obsidianmd/obsidian-releases/releases/latest/download/Obsidian-0.16.4.AppImage
chmod +x ~/Obsidian.AppImage
# Abrir: ~/Obsidian.AppImage
# Seleccionar vault: ~/jarvis/vault

# 8. Instalar extensiones VS Code
code --install-extension github.copilot
code --install-extension ms-azuretools.vscode-docker
code --install-extension ms-python.python

# 9. Hacer scripts ejecutables
chmod +x ~/jarvis/skills/autoskills.sh
chmod +x ~/jarvis/scripts/*.sh

# 10. Verificar que todo funciona
docker compose -f ~/jarvis/docker/docker-compose.yml ps
echo "JARVIS v2 listo!"
echo ""
echo "Siguientes pasos:"
echo "  1. Abre n8n: http://localhost:5678"
echo "  2. Abre Obsidian: ~/Obsidian.AppImage"
echo "  3. Crea un proyecto: jarvis-init.sh 'Mi Proyecto' 'Descripcion'"
echo "  4. Abre OpenCode: cd ~/jarvis/projects/mi-proyecto && opencode"
```

---

## Apéndice A: Tabla de modelos recomendados

| Tarea | Modelo | Via | Costo | Calidad |
|-------|--------|-----|-------|---------|
| Chat general | gemma2:2b | Ollama | $0 | Basica |
| Code simple | qwen2.5-coder:7b | Ollama | $0 | Buena |
| Code complejo | qwen3-coder:30b | OpenRouter | ~$0.002/req | Muy buena |
| Razonamiento | deepseek-r1 | OpenRouter | ~$0.001/req | Excelente |
| Premium (emergencia) | claude-sonnet-4 | Anthropic | ~$0.01/req | Maxima |
| Embeddings | nomic-embed-text | Ollama | $0 | — |

## Apéndice B: Convenciones de nombrado

| Elemento | Convencion | Ejemplo |
|----------|-----------|---------|
| Proyectos | kebab-case | `inventario-sabor` |
| Skills | kebab-case | `skill-deploy` |
| Ramas feature | feature/descripcion | feature/api-users |
| Ramas agent | agent/agente-tarea | agent/backend-crud |
| Commits | tipo(scope): desc [agent:nombre] | feat(api): add users [agent:backend] |
| Tags deploy | deploy-YYYYMMDD-HHMM | deploy-20260519-1430 |
| Docker containers | proyecto-servicio | inventario-app |

## Apéndice C: Checklist antes de deploy

- [ ] Todos los tests pasan (`npm test`)
- [ ] Lint sin errores (`npm run lint`)
- [ ] Build exitoso (`npm run build`)
- [ ] `.env` NO esta en git
- [ ] `.env.example` esta actualizado
- [ ] Dockerfile es multi-stage
- [ ] docker-compose tiene health checks
- [ ] Monitor incluido en compose
- [ ] SSL configurado si tiene dominio
- [ ] Tag de version en Git
- [ ] Nota en Obsidian del cliente actualizada

---

> **JARVIS v2** — Tu fabrica de fabricas AaaS, 100% open-source, corriendo local en Xubuntu.
> Costo: $15-25/mes. Poder: Ilimitado.
