/**
 * Sube las imágenes del catálogo a Medusa (File Module local -> static/) y las
 * anexa a la galería de cada producto, con un thumbnail principal.
 *
 *   cd src/medusa/apps/backend
 *   npx medusa exec ./src/scripts/upload-images.ts
 *
 * Fuente del mapeo: data/imagenes_map.json (de data/mapear_imagenes.py).
 * Las imágenes viven en drive-download (local, NO en git).
 *
 * Idempotente: si un producto ya tiene >= el nº de imágenes mapeadas y thumbnail,
 * se SALTA (no re-sube ni duplica). El "Precio<n>" del nombre NO toca precios.
 */
import { ExecArgs } from "@medusajs/framework/types"
import { ContainerRegistrationKeys } from "@medusajs/framework/utils"
import {
  uploadFilesWorkflow,
  updateProductsWorkflow,
} from "@medusajs/medusa/core-flows"
import { readFileSync, existsSync } from "fs"
import { resolve, basename, extname } from "path"

type MapEntry = {
  product_id: string
  handle: string
  name: string
  codigo_interno: string
  variacion: string
  match: string
}

function findRoot(): string {
  let dir = process.cwd()
  for (let i = 0; i < 8; i++) {
    if (existsSync(resolve(dir, "data", "imagenes_map.json"))) return dir
    dir = resolve(dir, "..")
  }
  throw new Error("No se encontró data/imagenes_map.json (corre mapear_imagenes.py)")
}

function mimeOf(file: string): string {
  const e = extname(file).toLowerCase()
  if (e === ".png") return "image/png"
  if (e === ".webp") return "image/webp"
  return "image/jpeg"
}

export default async function uploadImages({ container }: ExecArgs) {
  const logger = container.resolve(ContainerRegistrationKeys.LOGGER)
  const query = container.resolve(ContainerRegistrationKeys.QUERY)

  const root = findRoot()
  const map: Record<string, MapEntry> = JSON.parse(
    readFileSync(resolve(root, "data", "imagenes_map.json"), "utf-8")
  )

  // ---- Agrupar imágenes por external_id del producto ----
  // external_id = `${codigo}::${product_id}::${name}`.slice(0,250)  (igual que el seed)
  const byExternal = new Map<string, string[]>()
  for (const [rel, e] of Object.entries(map)) {
    const ext = `${e.codigo_interno}::${e.product_id}::${e.name}`.slice(0, 250)
    const abs = resolve(root, rel)
    if (!existsSync(abs)) continue
    const arr = byExternal.get(ext) || []
    arr.push(abs)
    byExternal.set(ext, arr)
  }
  // imágenes sin variación primero (foto principal -> thumbnail)
  for (const [, arr] of byExternal) {
    arr.sort((a, b) => {
      const av = /\([^)]*\)\.[^.]+$/.test(a) ? 1 : 0
      const bv = /\([^)]*\)\.[^.]+$/.test(b) ? 1 : 0
      return av - bv || basename(a).localeCompare(basename(b))
    })
  }
  logger.info(`Productos con imágenes mapeadas: ${byExternal.size}`)

  // ---- Productos existentes ----
  const { data: prods } = await query.graph({
    entity: "product",
    fields: ["id", "external_id", "thumbnail", "images.id"],
  })
  const prodByExternal = new Map<string, any>(
    prods.filter((p: any) => p.external_id).map((p: any) => [p.external_id, p])
  )

  let conImagen = 0
  let saltados = 0
  let subidas = 0
  let sinProducto = 0
  let i = 0

  for (const [ext, files] of byExternal) {
    i++
    const prod = prodByExternal.get(ext)
    if (!prod) {
      sinProducto++
      continue
    }
    const yaTiene = (prod.images || []).length
    if (yaTiene >= files.length && prod.thumbnail) {
      conImagen++
      saltados++
      continue
    }

    // subir archivos del producto
    const payload = files.map((abs) => ({
      filename: basename(abs),
      mimeType: mimeOf(abs),
      access: "public" as const,
      content: readFileSync(abs).toString("base64"),
    }))
    const { result: uploaded } = await uploadFilesWorkflow(container).run({
      input: { files: payload },
    })
    const urls = uploaded.map((u: any) => u.url)
    subidas += urls.length

    await updateProductsWorkflow(container).run({
      input: {
        products: [
          {
            id: prod.id,
            images: urls.map((url: string) => ({ url })),
            thumbnail: urls[0],
          },
        ],
      },
    })
    conImagen++
    if (i % 50 === 0 || i === byExternal.size) {
      logger.info(`  ...${i}/${byExternal.size} productos procesados (subidas acumuladas: ${subidas})`)
    }
  }

  logger.info(
    `=== UPLOAD COMPLETO: productos con imagen: ${conImagen} | saltados(idempotente): ${saltados} | imágenes subidas: ${subidas} | sin producto: ${sinProducto} ===`
  )
}
