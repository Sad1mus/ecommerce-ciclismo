# Backend Medusa (Fase 0). Build del monorepo (turbo -> @dtc/backend).
FROM node:20-slim AS build

# Herramientas para posibles modulos nativos (node-gyp).
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 make g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV NODE_ENV=development \
    npm_config_fund=false \
    npm_config_audit=false

# Manifiestos primero para cachear la instalacion.
COPY package.json package-lock.json turbo.json ./
COPY apps/backend/package.json apps/backend/package.json
RUN npm install

# Codigo y build (genera apps/backend/.medusa/server)
COPY . .
RUN npm run build

# ---- Imagen de runtime ----
FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production \
    PORT=9001
RUN useradd --create-home medusa
COPY --from=build --chown=medusa:medusa /app /app
USER medusa
EXPOSE 9001
WORKDIR /app/apps/backend
# DATABASE_URL/REDIS_URL/secrets por env en runtime. Migraciones + arranque.
CMD ["sh", "-c", "npx medusa db:migrate && npx medusa start"]
