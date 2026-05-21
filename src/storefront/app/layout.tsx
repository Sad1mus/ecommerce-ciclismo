import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tienda Ciclismo — Catálogo",
  description:
    "Catálogo de accesorios y repuestos de ciclismo. Precios y stock en tiempo real.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>
        <a className="skip-link" href="#contenido">
          Saltar al contenido principal
        </a>
        <header>
          <nav aria-label="Principal">
            <span className="brand">Tienda Ciclismo</span>
          </nav>
        </header>
        {children}
        <footer>
          <p>Precios y stock obtenidos en tiempo real desde el inventario.</p>
        </footer>
      </body>
    </html>
  );
}
