/**
 * Asegura una publishable API key ligada al sales channel por defecto y la imprime.
 * Idempotente: si ya existe una key del proyecto, la reutiliza.
 *
 *   cd src/medusa/apps/backend
 *   npx medusa exec ./src/scripts/ensure-publishable-key.ts
 *
 * El token resultante es el que consume el storefront (NEXT_PUBLIC_MEDUSA_PUBLISHABLE_KEY).
 * No es un secreto sensible (publishable), pero igual va por .env y no se hardcodea.
 */
import { ExecArgs } from "@medusajs/framework/types"
import { ContainerRegistrationKeys, Modules } from "@medusajs/framework/utils"
import {
  createApiKeysWorkflow,
  linkSalesChannelsToApiKeyWorkflow,
} from "@medusajs/medusa/core-flows"

const KEY_TITLE = "Storefront Ciclismo"

export default async function ensurePublishableKey({ container }: ExecArgs) {
  const query = container.resolve(ContainerRegistrationKeys.QUERY)
  const apiKeyModule = container.resolve(Modules.API_KEY)
  const scModule = container.resolve(Modules.SALES_CHANNEL)
  const logger = container.resolve(ContainerRegistrationKeys.LOGGER)

  // Sales channel del catalogo de ciclismo (el seed crea "Tienda Ciclismo");
  // si no existe, cae al primero disponible.
  const channels = await scModule.listSalesChannels({}, {})
  if (!channels.length) {
    throw new Error("No hay sales channel; corre el seed primero.")
  }
  const tienda = channels.find((c: any) => /tienda/i.test(c.name)) || channels[0]
  const salesChannelId = tienda.id

  // Buscar publishable key existente del proyecto
  const existing = await apiKeyModule.listApiKeys({
    type: "publishable",
    title: KEY_TITLE,
  })

  let token: string
  let keyId: string
  if (existing.length) {
    token = existing[0].token
    keyId = existing[0].id
    logger.info(`Publishable key existente reutilizada (${keyId}).`)
  } else {
    const { result } = await createApiKeysWorkflow(container).run({
      input: {
        api_keys: [{ title: KEY_TITLE, type: "publishable", created_by: "seed" }],
      },
    })
    token = result[0].token
    keyId = result[0].id
    logger.info(`Publishable key creada (${keyId}).`)
  }

  // La key debe quedar ligada a EXACTAMENTE UN sales channel; de lo contrario
  // la Store API no puede calcular disponibilidad de inventario. Quitamos
  // cualquier otro canal y nos aseguramos del enlace a "Tienda Ciclismo".
  const { data: linked } = await query.graph({
    entity: "publishable_api_key_sales_channel",
    fields: ["sales_channel_id"],
    filters: { publishable_key_id: keyId } as any,
  })
  const linkedIds = linked.map((l: any) => l.sales_channel_id)
  const remove = linkedIds.filter((id: string) => id !== salesChannelId)
  const add = linkedIds.includes(salesChannelId) ? [] : [salesChannelId]
  if (add.length || remove.length) {
    await linkSalesChannelsToApiKeyWorkflow(container).run({
      input: { id: keyId, add, remove },
    })
  }
  logger.info(`Canales tras ajuste: solo ${salesChannelId}`)

  logger.info(`SALES_CHANNEL_ID=${salesChannelId}`)
  // Marcador para extraer el token desde el stdout del script
  logger.info(`PUBLISHABLE_KEY_TOKEN=${token}`)
}
