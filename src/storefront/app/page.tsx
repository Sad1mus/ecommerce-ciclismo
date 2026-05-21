import { getCatalog, formatPrice } from "@/lib/medusa";

// Render dinamico: los datos se piden a la Store API en cada request
// (nunca en build), garantizando precios/stock reales y actuales.
export const dynamic = "force-dynamic";

export default async function HomePage() {
  const { products, count, ok } = await getCatalog(24);

  return (
    <main id="contenido">
      <h1>Catálogo de ciclismo</h1>

      {!ok && (
        <p role="alert" className="aviso">
          No fue posible cargar el catálogo en este momento. Dato no disponible;
          intenta de nuevo más tarde.
        </p>
      )}

      {ok && (
        <p className="resumen">
          Mostrando {products.length} de {count} productos disponibles.
        </p>
      )}

      {ok && products.length > 0 && (
        <ul className="catalogo" aria-label="Lista de productos">
          {products.map((p) => {
            const sinStock = p.stock !== null && p.stock <= 0;
            return (
              <li key={p.id} className="producto">
                <article aria-labelledby={`t-${p.id}`}>
                  <h2 id={`t-${p.id}`} className="producto-titulo">
                    {p.title}
                  </h2>
                  <p className="producto-precio">
                    <span className="etiqueta">Precio:</span>{" "}
                    {formatPrice(p.price)}
                  </p>
                  <p className="producto-stock">
                    <span className="etiqueta">Disponibilidad:</span>{" "}
                    {p.stock === null
                      ? "No disponible"
                      : sinStock
                        ? "Agotado"
                        : `${p.stock} en stock`}
                  </p>
                </article>
              </li>
            );
          })}
        </ul>
      )}
    </main>
  );
}
