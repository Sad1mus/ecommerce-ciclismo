# Goal Queue — Storefront Profesional Deportivo (Ecommerce Ciclismo)

estado: completada (5/5 done)
current: -
turn_cap_por_item: 35

<!--
Estados por tarea: [pending] -> [in-progress] -> [done] | [blocked]
Reglas:
- Solo UNA tarea [in-progress] a la vez. No empezar la siguiente hasta que la
  actual esté [done] o [blocked].
- "Check" debe CORRERSE y su resultado quedar VISIBLE en la conversación.
- Cada tarea termina con commit en rama `develop` + push a origin (NUNCA a main).
- Reglas permanentes:
  * ANTI-ALUCINACIÓN: precios/stock SIEMPRE desde la Store API de Medusa.
  * Accesibilidad: no degradar (el dueño es no vidente; debe seguir leíble por
    lector de pantalla aunque ahora también se vea bien).
  * Puertos locales: Postgres 5433, Redis 6380, Medusa 9001, storefront 8000.
  * Usar la publishable key y región COP YA creadas en el backend (no duplicar).
  * NO commitear node_modules, .env, ni secretos.
- Objetivo: reemplazar el storefront casero (3 archivos sin diseño) por el
  Starter oficial de Medusa, en español/COP, con tema DEPORTIVO Y ENÉRGICO.
-->

## [done] 1. Reemplazar por el Storefront oficial de Medusa y conectarlo
**Condición:** `src/storefront` pasa a ser el Next.js Starter oficial de Medusa
(medusajs/nextjs-starter-medusa), configurado contra el backend local (:9001) con
la publishable key y la región Colombia/COP ya existentes, y arranca mostrando los
608 productos reales. El storefront casero anterior queda en el historial git.
**Check (imprimir):**
- `cd src/storefront && npm install && npm run build` exit 0
- arrancar en :8000; `curl -s localhost:8000` → HTTP 200 y el catálogo (PLP) lista
  un producto REAL del inventario servido por la Store API
- `git log --oneline -1` en develop (commit pusheado)
**No tocar:** no romper el backend Medusa; usar la publishable key/region existentes
(no crear duplicados); no borrar el storefront viejo sin dejar commit previo.
**Evidencia:** Starter oficial (medusa-next, Next 15.3.9) instalado y conectado a :9001 con la
publishable key + región Colombia/COP existentes. `npm run build` exit 0 (917 páginas). Server :8000:
`/` → 307 → `/co` → HTTP 200; PLP `/co/store` HTTP 200 lista productos reales ("Pastilla freno comp
shimano", "Casco mtb plegable") con precios COP reales de la Store API ("COP 4,800", "COP 43,500").
Commit `cafe646` pusheado a develop. Storefront casero queda en historial (commit anterior c9835ba).

## [done] 2. Español + COP en toda la tienda
**Condición:** la UI está en español y los precios se muestran en COP formateados
(símbolo $ y separador de miles), con Colombia como región por defecto.
**Check (imprimir):**
- `npm run build` exit 0
- smoke: home, listado y página de producto muestran textos en español y un precio
  en COP real (ej. "$14.500"); sin textos en inglés visibles en home/PLP/PDP
- `git log --oneline -1` en develop
**No tocar:** precios desde la API (no hardcode); no romper el catálogo.
**Evidencia:** `npm run build` exit 0. Locale es-CO en convertToLocale + `<html lang=es>` + región
Colombia por defecto. Smoke a :8000: HOME `/co` 200 ("Tienda de Ciclismo y MTB", nav "Cuenta/Carrito",
footer "Categorías/Todos los derechos reservados"); PLP `/co/store` 200 ("Ordenar por", precios COP
"$ 4.800", "$ 43.500"); PDP `/co/products/pastilla-freno-comp-shimano` 200 ("Pastilla freno comp shimano",
"Agregar al carrito", precio "$ 14.500"). Cero inglés visible en home/PLP/PDP (solo la marca "Ciclismo
Store"). Commit `83be510` pusheado a develop.

## [done] 3. Tema DEPORTIVO Y ENÉRGICO (marca, colores, tipografía)
**Condición:** la tienda luce como una marca de ciclismo/MTB: paleta deportiva
(negro + acento neón naranja/verde), tipografía con carácter, header + hero potente,
tarjetas de producto atractivas, totalmente responsive (móvil y escritorio).
**Check (imprimir):**
- `npm run build` exit 0
- arrancar en :8000; `curl -s localhost:8000` → HTTP 200; mostrar que el tema aplica
  (p.ej. el CSS/clases del color de acento están presentes en el HTML/estilos)
- accesibilidad NO degradada: `npx @axe-core/cli http://localhost:8000` → 0
  violaciones critical/serious
- `git log --oneline -1` en develop
**No tocar:** no sacrificar accesibilidad por estética; contraste mínimo AA.
**Evidencia:** `npm run build` exit 0. Paleta brand-ink + acento naranja #FF6A00/lima #C6FF00,
tipografía Oswald+Inter (next/font), header oscuro, hero potente con CTA, tarjetas con hover. CSS
compilado contiene `#FF6A00`/`.btn-accent` y woff2 de Oswald; HTML home con btn-accent/text-brand-orange.
`npx @axe-core/cli http://localhost:8000` → **0 violaciones** (también PLP 0). Contrastes AA verificados
numéricamente. (axe corrió con Chrome-for-Testing en /tmp, fuera del repo). Commit `af50fe8` en develop.

## [done] 4. Búsqueda + navegación por categorías
**Condición:** búsqueda de productos por nombre y navegación por las 14 categorías,
ambas consultando la Store API (imprescindible con 608 productos).
**Check (imprimir):**
- `npm run build` exit 0
- smoke: buscar "guante" devuelve >=1 resultado real; abrir una categoría lista sus
  productos reales
- `git log --oneline -1` en develop
**No tocar:** búsqueda/categorías contra la API; anti-alucinación.
**Evidencia:** `npm run build` exit 0. Buscador en el header → `/co/search?q=guante` HTTP 200, "Resultados
para «guante»", **5 productos reales** (Guante mtb corto/largo/colores...). Categorías: `/co/categories/guantes`
200, y spot-check pastillas (12), pitillos (2), preventa-2025 (7) — todas 200 con productos reales; side
menu lista las 14 categorías. Búsqueda usa `/store/products?q=` de la Store API. axe 0 violaciones en home
y en /search. Commit `5a8c55f` en develop.

## [done] 5. Verificación final (build + accesibilidad + E2E) y cierre
**Condición:** la tienda nueva queda verde de punta a punta: build OK, accesibilidad
sin violaciones críticas, y un recorrido real (home → categoría → producto) muestra
datos reales de la API. Commit final en develop + push.
**Check (imprimir):**
- `npm run build` exit 0
- `npx @axe-core/cli http://localhost:8000` → 0 violaciones critical/serious
- `curl -s localhost:8000/<ruta-producto>` → HTTP 200 con nombre y precio COP reales
- `git log --oneline -1` en develop (commit pusheado)
**No tocar:** sin secretos; no desplegar; mantener anti-alucinación y accesibilidad.
**Evidencia:** Build limpio (`rm -rf .next && npm run build`) exit 0. `npx @axe-core/cli
http://localhost:8000` → **0 violaciones** (0 critical/serious). E2E real: `/` → 200 (/co, "Tienda de
ciclismo y MTB"); `/co/categories/guantes` → 200; producto `/co/products/guante-mtb-colores-corto` → 200
con nombre real "Guante mtb colores corto" y precio COP real "$ 14.500" (desde la Store API). No se
desplegó. Cierre en develop (último commit de código `5a8c55f`; commit de cierre con esta evidencia).
