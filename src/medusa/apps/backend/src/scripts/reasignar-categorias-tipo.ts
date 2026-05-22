/**
 * Reasigna los productos a categorías de COMPRA POR TIPO (legibles para el cliente)
 * derivadas del nombre, a partir de data/categorias_map.json (generado por
 * data/clasificar_categorias.py).
 *
 *   cd src/medusa/apps/backend
 *   npx medusa exec ./src/scripts/reasignar-categorias-tipo.ts
 *
 * Qué hace (idempotente / re-ejecutable):
 *  1. Crea las categorías-tipo que falten (por nombre).
 *  2. A cada producto (cruzado por external_id) le pone como ÚNICA categoría su
 *     tipo, y guarda el código interno original (6-CL, 1-RK, ...) en
 *     product.metadata.codigo_interno  (NO se pierde, solo deja de ser categoría).
 *  3. Desactiva (is_active=false) las categorías-código antiguas para que dejen de
 *     verse en la navegación / Store API.
 *
 * ANTI-ALUCINACIÓN: no toca precios ni stock; el tipo es la derivación ya
 * calculada y revisada en categorias_map.json. Solo mueve asociaciones de categoría
 * y escribe metadata.
 */
import { ExecArgs } from "@medusajs/framework/types"
import { ContainerRegistrationKeys } from "@medusajs/framework/utils"
import {
  createProductCategoriesWorkflow,
  updateProductCategoriesWorkflow,
  updateProductsWorkflow,
} from "@medusajs/medusa/core-flows"
import { readFileSync, existsSync } from "fs"
import { resolve } from "path"

type MapEntry = {
  product_id: string
  handle: string
  name: string
  tipo: string
  codigo_interno: string
}

const BATCH = 100

function slugify(s: string): string {
  return s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80)
    .replace(/-+$/g, "")
}

function findMapJson(): string {
  let dir = process.cwd()
  for (let i = 0; i < 8; i++) {
    const p = resolve(dir, "data", "categorias_map.json")
    if (existsSync(p)) return p
    dir = resolve(dir, "..")
  }
  throw new Error("No se encontró data/categorias_map.json (corre clasificar_categorias.py)")
}

export default async function reasignar({ container }: ExecArgs) {
  const logger = container.resolve(ContainerRegistrationKeys.LOGGER)
  const query = container.resolve(ContainerRegistrationKeys.QUERY)

  const jsonPath = findMapJson()
  const map: Record<string, MapEntry> = JSON.parse(readFileSync(jsonPath, "utf-8"))
  const entries = Object.entries(map)
  logger.info(`Mapa: ${entries.length} productos desde ${jsonPath}`)

  const tipos = [...new Set(entries.map(([, e]) => e.tipo))].sort()
  const codigos = [...new Set(entries.map(([, e]) => e.codigo_interno))].sort()
  logger.info(`Tipos a asegurar: ${tipos.length} | códigos internos antiguos: ${codigos.length}`)

  // ---- 1. Categorías existentes ----
  const { data: existingCats } = await query.graph({
    entity: "product_category",
    fields: ["id", "name", "handle", "is_active"],
  })
  const catByName = new Map<string, any>(existingCats.map((c: any) => [c.name, c]))
  // handles ya ocupados (incl. categorías-código como "guantes" de GUANTES);
  // los handles son únicos aunque la categoría esté inactiva.
  const usedHandles = new Set<string>(existingCats.map((c: any) => c.handle).filter(Boolean))

  // ---- 2. Crear tipos faltantes (handle explícito, sin chocar con códigos) ----
  const missing = tipos.filter((t) => !catByName.has(t))
  if (missing.length) {
    const payload = missing.map((name) => {
      let h = slugify(name)
      while (usedHandles.has(h)) h = `${h}-tipo`
      usedHandles.add(h)
      return { name, handle: h, is_active: true }
    })
    const { result } = await createProductCategoriesWorkflow(container).run({
      input: { product_categories: payload },
    })
    result.forEach((c: any) => catByName.set(c.name, c))
    logger.info(`Categorías-tipo creadas: ${missing.length} -> ${missing.join(", ")}`)
  } else {
    logger.info("Categorías-tipo ya existían (idempotente)")
  }

  // ---- 3. Cruce productos por external_id ----
  const { data: prods } = await query.graph({
    entity: "product",
    fields: ["id", "external_id", "metadata"],
  })
  const prodByExternal = new Map<string, any>(
    prods.filter((p: any) => p.external_id).map((p: any) => [p.external_id, p])
  )

  const updates: any[] = []
  let sinCruce = 0
  for (const [externalId, e] of entries) {
    const prod = prodByExternal.get(externalId)
    if (!prod) {
      sinCruce++
      continue
    }
    const tipoId = catByName.get(e.tipo)!.id
    updates.push({
      id: prod.id,
      category_ids: [tipoId],
      metadata: { ...(prod.metadata || {}), codigo_interno: e.codigo_interno },
    })
  }
  logger.info(`Productos a reasignar: ${updates.length} (sin cruce: ${sinCruce})`)

  // ---- 4. Aplicar en lotes ----
  let done = 0
  for (let i = 0; i < updates.length; i += BATCH) {
    const chunk = updates.slice(i, i + BATCH)
    await updateProductsWorkflow(container).run({ input: { products: chunk } })
    done += chunk.length
    logger.info(`  ...${done}/${updates.length} productos reasignados`)
  }

  // ---- 5. Desactivar categorías-código antiguas ----
  const toDeactivate = codigos
    .map((c) => catByName.get(c))
    .filter((c) => c && c.is_active !== false)
    .map((c) => c.id)
  if (toDeactivate.length) {
    await updateProductCategoriesWorkflow(container).run({
      input: { selector: { id: toDeactivate }, update: { is_active: false } },
    })
    logger.info(`Categorías-código desactivadas: ${toDeactivate.length}`)
  } else {
    logger.info("Categorías-código ya estaban inactivas (idempotente)")
  }

  logger.info(
    `=== REASIGNACIÓN COMPLETA: categorías-tipo=${tipos.length} productos asignados=${updates.length} ===`
  )
}
