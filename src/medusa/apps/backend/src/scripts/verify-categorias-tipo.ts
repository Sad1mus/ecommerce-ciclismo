/**
 * Verificación de la reasignación a categorías-tipo (no muta nada).
 *   npx medusa exec ./src/scripts/verify-categorias-tipo.ts
 */
import { ExecArgs } from "@medusajs/framework/types"
import { ContainerRegistrationKeys } from "@medusajs/framework/utils"

const CODIGOS = ["1-RK", "1.1-KL", "2-SPK", "3-RR", "4-BK", "5-MT", "6-CL",
  "GUANTES", "PASTILLAS", "PITILLOS", "PREVENTA 2025", "PRODUCTOS P 2025",
  "PRODUTOS TORNASOL", "UÑAS"]

export default async function verify({ container }: ExecArgs) {
  const logger = container.resolve(ContainerRegistrationKeys.LOGGER)
  const query = container.resolve(ContainerRegistrationKeys.QUERY)

  // 1. Producto conocido CL128
  const { data: cl128 } = await query.graph({
    entity: "product",
    fields: ["id", "title", "metadata", "categories.name", "categories.is_active"],
    filters: { external_id: "1-RK::CL128::Candado manguera espiral" } as any,
  })
  const p = cl128[0]
  logger.info(
    `CL128 "${p?.title}" -> categorías=${JSON.stringify((p?.categories || []).map((c: any) => c.name))} | metadata.codigo_interno=${p?.metadata?.codigo_interno}`
  )

  // 2. Categorías activas vs inactivas
  const { data: cats } = await query.graph({
    entity: "product_category",
    fields: ["name", "is_active"],
  })
  const activas = cats.filter((c: any) => c.is_active).map((c: any) => c.name).sort()
  const codigosActivos = activas.filter((n: string) => CODIGOS.includes(n))
  logger.info(`Categorías ACTIVAS (${activas.length}): ${JSON.stringify(activas)}`)
  logger.info(`Códigos internos AÚN activos (debe ser 0): ${JSON.stringify(codigosActivos)}`)

  // 3. Conteo de productos por categoría-tipo activa
  const { data: withCat } = await query.graph({
    entity: "product",
    fields: ["id", "categories.name", "categories.is_active"],
  })
  const conteo: Record<string, number> = {}
  for (const pr of withCat) {
    for (const c of (pr as any).categories || []) {
      if (c.is_active) conteo[c.name] = (conteo[c.name] || 0) + 1
    }
  }
  logger.info("PRODUCTOS POR CATEGORÍA-TIPO ACTIVA:")
  for (const [name, n] of Object.entries(conteo).sort((a, b) => b[1] - a[1])) {
    logger.info(`  ${String(n).padStart(4)}  ${name}`)
  }

  const ok =
    p?.metadata?.codigo_interno === "1-RK" &&
    (p?.categories || []).some((c: any) => c.name === "Candados") &&
    codigosActivos.length === 0
  logger.info(`RESULTADO VERIFICACIÓN: ${ok ? "OK" : "FALLA"}`)
}
