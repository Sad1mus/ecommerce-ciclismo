/**
 * Verifica la subida de imágenes (no muta nada).
 *   npx medusa exec ./src/scripts/verify-images.ts
 */
import { ExecArgs } from "@medusajs/framework/types"
import { ContainerRegistrationKeys } from "@medusajs/framework/utils"

export default async function verifyImages({ container }: ExecArgs) {
  const logger = container.resolve(ContainerRegistrationKeys.LOGGER)
  const query = container.resolve(ContainerRegistrationKeys.QUERY)

  const { data: prods } = await query.graph({
    entity: "product",
    fields: ["id", "external_id", "thumbnail", "images.url"],
  })
  const total = prods.length
  const conImagen = prods.filter((p: any) => (p.images || []).length > 0).length
  const conThumb = prods.filter((p: any) => p.thumbnail).length
  logger.info(`Productos: ${total} | con >=1 imagen: ${conImagen} | con thumbnail: ${conThumb}`)

  const cl = prods.find(
    (p: any) => p.external_id === "1-RK::CL128::Candado manguera espiral"
  )
  logger.info(
    `CL128: imágenes=${(cl?.images || []).length} thumbnail=${cl?.thumbnail || "(none)"}`
  )
  if (cl?.images?.[0]) logger.info(`CL128 primera imagen url: ${cl.images[0].url}`)

  const ok = conImagen >= 540 && (cl?.images || []).length >= 1
  logger.info(`RESULTADO IMÁGENES: ${ok ? "OK" : "FALLA"} (umbral con-imagen>=540)`)
}
