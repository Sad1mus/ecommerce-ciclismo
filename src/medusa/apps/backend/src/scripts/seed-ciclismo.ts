/**
 * Seed del inventario de ciclismo desde data/inventario.json (generado por
 * data/normalize_inventory.py a partir del CSV del admin).
 *
 * Re-ejecutable (idempotente por SKU): si un producto ya existe, lo salta.
 * Asi anexar un inventario nuevo = regenerar el JSON y volver a correr.
 *
 *   cd src/medusa/apps/backend
 *   npx medusa exec ./src/scripts/seed-ciclismo.ts
 *
 * Reglas del proyecto:
 *  - Precios y stock salen del JSON (fuente del admin), nunca inventados aqui.
 *  - Variantes con precio estimado o $0 -> producto en estado "draft"
 *    (visible para el admin, NO comprable hasta confirmar precio).
 *  - Moneda COP, sin subunidad (amount = pesos enteros).
 */
import { ExecArgs } from "@medusajs/framework/types"
import {
  ContainerRegistrationKeys,
  Modules,
  ProductStatus,
} from "@medusajs/framework/utils"
import {
  createProductCategoriesWorkflow,
  createProductsWorkflow,
  createRegionsWorkflow,
  createSalesChannelsWorkflow,
  createStockLocationsWorkflow,
  createShippingProfilesWorkflow,
  createInventoryLevelsWorkflow,
  updateStoresWorkflow,
} from "@medusajs/medusa/core-flows"
import { readFileSync, existsSync } from "fs"
import { resolve } from "path"

type Variant = {
  variation: string
  price_cop: number
  price_source: string
  stock: number
  sellable: boolean
}
type Product = {
  category: string
  product_id: string
  name: string
  variants: Variant[]
}

const CURRENCY = "cop"
const BATCH = 100

function findInventoryJson(): string {
  // sube directorios buscando data/inventario.json
  let dir = process.cwd()
  for (let i = 0; i < 8; i++) {
    const p = resolve(dir, "data", "inventario.json")
    if (existsSync(p)) return p
    dir = resolve(dir, "..")
  }
  throw new Error("No se encontro data/inventario.json (corre normalize_inventory.py)")
}

function sanitizeSku(s: string): string {
  return s.toUpperCase().replace(/[^A-Z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40)
}

function slugify(s: string): string {
  return s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "") // quita acentos
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80)
    .replace(/-+$/g, "") // por si el slice dejo guion final
}

export default async function seedCiclismo({ container }: ExecArgs) {
  const logger = container.resolve(ContainerRegistrationKeys.LOGGER)
  const query = container.resolve(ContainerRegistrationKeys.QUERY)
  const salesChannelModule = container.resolve(Modules.SALES_CHANNEL)
  const storeModule = container.resolve(Modules.STORE)

  const jsonPath = findInventoryJson()
  const products: Product[] = JSON.parse(readFileSync(jsonPath, "utf-8"))
  logger.info(`Inventario: ${products.length} productos desde ${jsonPath}`)

  // ---- 1. Store: habilitar COP como moneda por defecto ----
  const [store] = await storeModule.listStores()
  await updateStoresWorkflow(container).run({
    input: {
      selector: { id: store.id },
      update: {
        supported_currencies: [{ currency_code: CURRENCY, is_default: true }],
      },
    },
  })
  logger.info("Moneda COP habilitada en el store")

  // ---- 2. Sales channel por defecto ----
  let [salesChannel] = await salesChannelModule.listSalesChannels({
    name: "Tienda Ciclismo",
  })
  if (!salesChannel) {
    const { result } = await createSalesChannelsWorkflow(container).run({
      input: { salesChannelsData: [{ name: "Tienda Ciclismo" }] },
    })
    salesChannel = result[0]
  }

  // ---- 3. Region Colombia (COP) ----
  const { data: regions } = await query.graph({
    entity: "region",
    fields: ["id", "name"],
  })
  if (!regions.find((r: any) => r.name === "Colombia")) {
    await createRegionsWorkflow(container).run({
      input: {
        regions: [
          {
            name: "Colombia",
            currency_code: CURRENCY,
            countries: ["co"],
            payment_providers: ["pp_system_default"],
          },
        ],
      },
    })
    logger.info("Region Colombia creada")
  }

  // ---- 4. Stock location: Bodega Principal ----
  const { data: locations } = await query.graph({
    entity: "stock_location",
    fields: ["id", "name"],
  })
  let stockLocationId = locations.find((l: any) => l.name === "Bodega Principal")?.id
  if (!stockLocationId) {
    const { result } = await createStockLocationsWorkflow(container).run({
      input: { locations: [{ name: "Bodega Principal", address: { country_code: "co", city: "Bogota", address_1: "Bodega" } }] },
    })
    stockLocationId = result[0].id
    logger.info("Stock location 'Bodega Principal' creada")
  }

  // ---- 5. Shipping profile por defecto ----
  const { data: profiles } = await query.graph({
    entity: "shipping_profile",
    fields: ["id", "name"],
  })
  let shippingProfileId = profiles[0]?.id
  if (!shippingProfileId) {
    const { result } = await createShippingProfilesWorkflow(container).run({
      input: { data: [{ name: "Default", type: "default" }] },
    })
    shippingProfileId = result[0].id
  }

  // ---- 6. Categorias ----
  const catNames = [...new Set(products.map((p) => p.category))].sort()
  const { data: existingCats } = await query.graph({
    entity: "product_category",
    fields: ["id", "name"],
  })
  const catMap = new Map<string, string>(existingCats.map((c: any) => [c.name, c.id]))
  const missing = catNames.filter((n) => !catMap.has(n))
  if (missing.length) {
    const { result } = await createProductCategoriesWorkflow(container).run({
      input: { product_categories: missing.map((name) => ({ name, is_active: true })) },
    })
    result.forEach((c: any) => catMap.set(c.name, c.id))
    logger.info(`${missing.length} categorias creadas`)
  }

  // ---- 7. SKUs unicos + payload de productos ----
  const { data: existingProds } = await query.graph({
    entity: "product",
    fields: ["id", "external_id"],
  })
  const existingExternal = new Set(existingProds.map((p: any) => p.external_id).filter(Boolean))

  const usedSku = new Set<string>()
  const usedHandle = new Set<string>()
  let sinCounter = 0
  const stockBySku = new Map<string, number>()

  const productPayloads: any[] = []
  for (const p of products) {
    const externalId = `${p.category}::${p.product_id}::${p.name}`.slice(0, 250)
    if (existingExternal.has(externalId)) continue // ya sembrado

    const base = p.product_id === "SIN_ID" ? `SIN-${String(++sinCounter).padStart(3, "0")}` : p.product_id
    const optionValues = p.variants.map((v) => v.variation)
    const allSellable = p.variants.every((v) => v.sellable)

    const variants = p.variants.map((v) => {
      let sku = sanitizeSku(`${base}-${v.variation}`)
      while (usedSku.has(sku)) sku = `${sku}-X`
      usedSku.add(sku)
      stockBySku.set(sku, v.stock)
      return {
        title: v.variation,
        sku,
        manage_inventory: true,
        prices: [{ amount: v.price_cop, currency_code: CURRENCY }],
        options: { "Variación": v.variation },
      }
    })

    // handle URL-safe y unico (Medusa lo exige; el autogenerado fallaba con
    // titulos que terminan en espacio/caracter especial)
    let handle = slugify(p.name) || sanitizeSku(base).toLowerCase() || `prod-${base.toLowerCase()}`
    let h = handle
    let hn = 1
    while (usedHandle.has(h)) h = `${handle}-${++hn}`
    usedHandle.add(h)

    productPayloads.push({
      title: p.name,
      handle: h,
      external_id: externalId,
      status: allSellable ? ProductStatus.PUBLISHED : ProductStatus.DRAFT,
      category_ids: [catMap.get(p.category)!],
      shipping_profile_id: shippingProfileId,
      sales_channels: [{ id: salesChannel.id }],
      options: [{ title: "Variación", values: [...new Set(optionValues)] }],
      variants,
    })
  }

  logger.info(`Productos nuevos a crear: ${productPayloads.length}`)

  // ---- 8. Crear productos por lotes ----
  let created = 0
  for (let i = 0; i < productPayloads.length; i += BATCH) {
    const chunk = productPayloads.slice(i, i + BATCH)
    await createProductsWorkflow(container).run({ input: { products: chunk } })
    created += chunk.length
    logger.info(`  ...${created}/${productPayloads.length} productos`)
  }

  // ---- 9. Niveles de inventario por SKU (stock real del CSV) ----
  const { data: invItems } = await query.graph({
    entity: "inventory_item",
    fields: ["id", "sku"],
  })
  const levels = invItems
    .filter((ii: any) => stockBySku.has(ii.sku))
    .map((ii: any) => ({
      location_id: stockLocationId,
      inventory_item_id: ii.id,
      stocked_quantity: stockBySku.get(ii.sku)!,
    }))
  if (levels.length) {
    for (let i = 0; i < levels.length; i += BATCH) {
      await createInventoryLevelsWorkflow(container).run({
        input: { inventory_levels: levels.slice(i, i + BATCH) },
      })
    }
    logger.info(`Niveles de inventario creados: ${levels.length}`)
  }

  logger.info("=== SEED CICLISMO COMPLETO ===")
}
