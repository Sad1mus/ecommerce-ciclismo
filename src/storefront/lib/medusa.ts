/**
 * Cliente de la Store API de Medusa.
 *
 * REGLA ANTI-ALUCINACION del proyecto: los precios y el stock SIEMPRE provienen
 * de esta API (fuente = DB de Medusa). Nunca se inventan ni se hardcodean en el
 * storefront. Si la API falla, devolvemos lista vacia + flag de error y la UI
 * muestra un aviso, jamas datos ficticios.
 */

const BACKEND_URL =
  process.env.MEDUSA_BACKEND_URL || "http://localhost:9001";
const PUBLISHABLE_KEY = process.env.MEDUSA_PUBLISHABLE_KEY || "";
const REGION_ID = process.env.MEDUSA_REGION_ID || "";

export type Price = {
  amount: number;
  currency: string;
} | null;

export type Product = {
  id: string;
  title: string;
  price: Price;
  stock: number | null;
};

export type CatalogResult = {
  products: Product[];
  count: number;
  ok: boolean;
};

type RawVariant = {
  inventory_quantity?: number | null;
  calculated_price?: {
    calculated_amount?: number | null;
    currency_code?: string | null;
  } | null;
};

type RawProduct = {
  id: string;
  title: string;
  variants?: RawVariant[] | null;
};

export async function getCatalog(limit = 24): Promise<CatalogResult> {
  if (!PUBLISHABLE_KEY) {
    return { products: [], count: 0, ok: false };
  }

  const params = new URLSearchParams({
    limit: String(limit),
    fields:
      "id,title,*variants,+variants.calculated_price,+variants.inventory_quantity",
  });
  if (REGION_ID) params.set("region_id", REGION_ID);

  try {
    const res = await fetch(`${BACKEND_URL}/store/products?${params}`, {
      headers: { "x-publishable-api-key": PUBLISHABLE_KEY },
      cache: "no-store",
    });
    if (!res.ok) return { products: [], count: 0, ok: false };

    const data = (await res.json()) as {
      products: RawProduct[];
      count: number;
    };

    const products: Product[] = (data.products || []).map((p) => {
      const v = (p.variants || [])[0];
      const cp = v?.calculated_price;
      const price: Price =
        cp && typeof cp.calculated_amount === "number"
          ? {
              amount: cp.calculated_amount,
              currency: (cp.currency_code || "cop").toUpperCase(),
            }
          : null;
      const stock =
        typeof v?.inventory_quantity === "number"
          ? v.inventory_quantity
          : null;
      return { id: p.id, title: p.title, price, stock };
    });

    return { products, count: data.count ?? products.length, ok: true };
  } catch {
    return { products: [], count: 0, ok: false };
  }
}

export function formatPrice(price: Price): string {
  if (!price) return "Precio no disponible";
  // COP sin subunidad: entero en pesos.
  const formatted = new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: price.currency,
    maximumFractionDigits: 0,
  }).format(price.amount);
  return formatted;
}
