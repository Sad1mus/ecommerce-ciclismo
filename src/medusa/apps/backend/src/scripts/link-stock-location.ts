/**
 * Liga el stock location al sales channel "Tienda Ciclismo" para que la Store API
 * pueda calcular la disponibilidad (inventory_quantity) de cada variante.
 * Idempotente.
 */
import { ExecArgs } from "@medusajs/framework/types"
import { ContainerRegistrationKeys, Modules } from "@medusajs/framework/utils"
import { linkSalesChannelsToStockLocationWorkflow } from "@medusajs/medusa/core-flows"

export default async function linkStock({ container }: ExecArgs) {
  const sc = container.resolve(Modules.SALES_CHANNEL)
  const stock = container.resolve(Modules.STOCK_LOCATION)
  const query = container.resolve(ContainerRegistrationKeys.QUERY)
  const logger = container.resolve(ContainerRegistrationKeys.LOGGER)

  const channels = await sc.listSalesChannels({}, {})
  const tienda = channels.find((c: any) => /tienda/i.test(c.name)) || channels[0]

  const locations = await stock.listStockLocations({}, {})
  if (!locations.length) throw new Error("No hay stock location.")
  logger.info("LOCATIONS: " + JSON.stringify(locations.map((l: any) => l.name)))
  // El seed deposita el inventario real en "Bodega Principal".
  const loc =
    locations.find((l: any) => /bodega principal/i.test(l.name)) || locations[0]

  const { data: existing } = await query.graph({
    entity: "sales_channel_location",
    fields: ["stock_location_id"],
    filters: { sales_channel_id: tienda.id } as any,
  })
  const already = existing.some((l: any) => l.stock_location_id === loc.id)
  if (!already) {
    await linkSalesChannelsToStockLocationWorkflow(container).run({
      input: { id: loc.id, add: [tienda.id] },
    })
    logger.info(`Enlazado stock location ${loc.id} -> sales channel ${tienda.id}`)
  } else {
    logger.info(`Stock location ya enlazado a ${tienda.id}`)
  }
}
