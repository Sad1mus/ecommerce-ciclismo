import { ExecArgs } from "@medusajs/framework/types"
import { ContainerRegistrationKeys, Modules } from "@medusajs/framework/utils"

export default async function diag({ container }: ExecArgs) {
  const query = container.resolve(ContainerRegistrationKeys.QUERY)
  const sc = container.resolve(Modules.SALES_CHANNEL)
  const logger = container.resolve(ContainerRegistrationKeys.LOGGER)

  const channels = await sc.listSalesChannels({}, {})
  logger.info("SALES CHANNELS: " + JSON.stringify(channels.map((c: any) => [c.id, c.name])))

  const { data: byStatus } = await query.graph({
    entity: "product",
    fields: ["id", "status"],
  })
  const counts: Record<string, number> = {}
  for (const p of byStatus) counts[p.status] = (counts[p.status] || 0) + 1
  logger.info("PRODUCTS BY STATUS: " + JSON.stringify(counts))

  // productos por sales channel
  for (const c of channels) {
    const { data } = await query.graph({
      entity: "product",
      fields: ["id"],
      filters: { sales_channels: { id: c.id }, status: "published" } as any,
    })
    logger.info(`PUBLISHED IN CHANNEL ${c.name} (${c.id}): ${data.length}`)
  }
}
