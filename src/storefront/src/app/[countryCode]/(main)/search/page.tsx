import { Metadata } from "next"

import { listProducts } from "@lib/data/products"
import { getRegion } from "@lib/data/regions"
import ProductPreview from "@modules/products/components/product-preview"

export const metadata: Metadata = {
  title: "Búsqueda",
  description: "Busca productos en nuestra tienda.",
}

type Params = {
  searchParams: Promise<{ q?: string }>
  params: Promise<{ countryCode: string }>
}

export default async function SearchPage(props: Params) {
  const { countryCode } = await props.params
  const { q } = await props.searchParams
  const query = (q ?? "").trim()

  const region = await getRegion(countryCode)

  const { products } = query && region
    ? (
        await listProducts({
          countryCode,
          queryParams: { q: query, limit: 24 },
        })
      ).response
    : { products: [] }

  return (
    <div className="content-container py-10" data-testid="search-container">
      <div className="mb-8">
        <span className="accent-bar" aria-hidden="true" />
        <h1
          className="font-display text-3xl uppercase mt-3 text-brand-ink"
          data-testid="search-page-title"
        >
          {query ? <>Resultados para «{query}»</> : "Buscar productos"}
        </h1>
        {query && (
          <p className="text-ui-fg-subtle mt-1" data-testid="search-count">
            {products.length} resultado{products.length === 1 ? "" : "s"}
          </p>
        )}
      </div>

      {!query ? (
        <p className="text-ui-fg-subtle">
          Escribe el nombre de un producto en el buscador para ver resultados.
        </p>
      ) : products.length === 0 ? (
        <p className="text-ui-fg-subtle" data-testid="no-results">
          No encontramos productos para «{query}». Prueba con otra palabra.
        </p>
      ) : (
        <ul
          className="grid grid-cols-2 w-full small:grid-cols-3 medium:grid-cols-4 gap-x-6 gap-y-8"
          data-testid="search-results"
        >
          {products.map((p) => (
            <li key={p.id}>
              <ProductPreview product={p} region={region!} />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
