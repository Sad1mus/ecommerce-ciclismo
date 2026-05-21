/**
 * Borra los productos y categorias demo que trae Medusa por defecto
 * (Medusa T-Shirt/Sweatshirt/Sweatpants/Shorts, categorias Shirts/Pants/
 * Merch/Sweatshirts). Los nuestros tienen external_id; los demo no.
 *
 *   npx medusa exec ./src/scripts/clean-demo.ts
 */
import { ExecArgs } from "@medusajs/framework/types"
import { ContainerRegistrationKeys } from "@medusajs/framework/utils"
import {
  deleteProductsWorkflow,
  deleteProductCategoriesWorkflow,
} from "@medusajs/medusa/core-flows"

const DEMO_CATEGORIES = ["Shirts", "Pants", "Merch", "Sweatshirts"]

export default async function cleanDemo({ container }: ExecArgs) {
  const logger = container.resolve(ContainerRegistrationKeys.LOGGER)
  const query = container.resolve(ContainerRegistrationKeys.QUERY)

  const { data: products } = await query.graph({
    entity: "product",
    fields: ["id", "title", "external_id"],
  })
  const demoIds = products
    .filter((p: any) => !p.external_id)
    .map((p: any) => p.id)
  if (demoIds.length) {
    await deleteProductsWorkflow(container).run({ input: { ids: demoIds } })
    logger.info(`Productos demo borrados: ${demoIds.length}`)
  } else {
    logger.info("No hay productos demo")
  }

  const { data: cats } = await query.graph({
    entity: "product_category",
    fields: ["id", "name"],
  })
  const demoCatIds = cats
    .filter((c: any) => DEMO_CATEGORIES.includes(c.name))
    .map((c: any) => c.id)
  if (demoCatIds.length) {
    await deleteProductCategoriesWorkflow(container).run({ input: demoCatIds })
    logger.info(`Categorias demo borradas: ${demoCatIds.length}`)
  }

  logger.info("=== LIMPIEZA DEMO COMPLETA ===")
}
