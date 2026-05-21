# Storefront Next.js (Fase 1). Build multi-stage con salida standalone.
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# El catalogo se pide a la Store API en runtime (pagina dinamica), no en build.
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=8000
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001
# Artefactos minimos de la salida standalone
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 8000
# MEDUSA_BACKEND_URL / MEDUSA_PUBLISHABLE_KEY / MEDUSA_REGION_ID por env en runtime
CMD ["node", "server.js"]
