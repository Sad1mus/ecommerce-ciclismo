# Goal Queue — Contenido del Catálogo (Categorías + Imágenes) — Ecommerce Ciclismo

estado: completada
current: 6
turn_cap_por_item: 30

<!--
Cola FUSIONADA: primero categorías de compra legibles (Fase A, tareas 1-3),
luego imágenes del catálogo (Fase B, tareas 4-6). Secuencial: ambas tocan Medusa,
por eso van en una sola cola y nunca en paralelo.

Necesita VIVOS: Postgres 5433, Redis 6380, Medusa 9001, storefront 8000.

Estados por tarea: [pending] -> [in-progress] -> [done] | [blocked]
Reglas:
- Solo UNA tarea [in-progress] a la vez. No empezar la siguiente hasta [done]/[blocked].
- "Check" debe CORRERSE y su resultado quedar VISIBLE en la conversación.
- Cada tarea termina con commit en rama `develop` + push a origin (NUNCA a main).
- ANTI-ALUCINACIÓN: clasificar por nombre y mapear imágenes son DERIVACIONES, no se
  inventan datos; stock y precios NO se tocan. El "Precio" del nombre de archivo es
  solo metadato para identificar. Lo dudoso se LISTA para el dueño, no se adivina.
- NO commitear: imágenes, carpeta drive-download, binarios subidos, node_modules,
  .env, secretos (gitignorear lo que aplique).

=================== FASE A — CATEGORÍAS DE COMPRA POR TIPO ===================
Problema: hoy las categorías visibles para el cliente y el lector de pantalla SON
los códigos internos del dueño (6-CL, 1-RK, 2-SPK, 3-RR, 4-BK, 5-MT, 1.1-KL...).
Son crípticos ("seis-guion-ce-ele") y NO son tipos de producto (los mismos tipos se
reparten entre varios códigos -> son códigos de proveedor/lote/estante).
Solución: categorías por TIPO derivadas del NOMBRE (Bolsos, Bombas e infladores,
Candados, Gafas, Guantes, Cascos, Frenos y pastillas, Sillines, Manubrios y potencias,
Transmisión (cadenas/coronillas/piñones), Llantas rines y aros, Pedales, Luces,
Mangos/grips, Kits de reparación, Accesorios de manubrio, Puntas de marco, etc.).
El código interno (6-CL...) se conserva como METADATO oculto del producto.
==============================================================================
-->

## [done] 1. Clasificador nombre→tipo + reporte de cobertura
**Condición:** un script clasifica los 608 productos en categorías de compra por tipo,
a partir de reglas sobre el nombre, y genera `data/categorias_map.json`
(product_id/handle -> tipo + código_interno original). Reporte visible con cobertura;
lo no clasificable cae en "Otros / por clasificar" y se LISTA para el dueño.
**Check (imprimir):**
- correr el script: imprime "clasificados X/608" con X >= 548 (>=90%) y la lista de
  productos en "Otros / por clasificar"
- imprime el conteo por tipo (ej. Bombas: N, Sillines: N, ...)
- `data/categorias_map.json` generado; `git log --oneline -1` en develop
**No tocar:** no inventar tipos para lo dudoso (va a "Otros"); no tocar precios/stock.
**Evidencia:** `data/clasificar_categorias.py` clasifica 549/608 (90.3% ≥548) en 22 tipos
legibles; 59 dudosos LISTADOS en "Otros / por clasificar" (colores sueltos, tapabocas,
bicis exhibición, llaveros, abrazaderas/espaciadores). `data/categorias_map.json` con 608
entradas (external_id→tipo+codigo_interno; CL128→Candados, codigo_interno=1-RK). Commit
ec21f9e en develop (pusheado); drive-download e imágenes gitignoreados.

## [done] 2. Crear categorías de TIPO en Medusa + reasignar productos
**Condición:** las categorías de compra por tipo existen en Medusa y cada producto
queda asignado a la suya; el código interno original (6-CL...) se guarda en
`product.metadata.codigo_interno`. Las categorías-código antiguas dejan de ser
visibles para el cliente (inactivas o fuera de la navegación). Re-ejecutable.
**Check (imprimir):**
- `npx medusa exec ...` exit 0; imprime nº de categorías tipo creadas y productos asignados
- query a Medusa: un producto conocido (CL128 "Candado manguera espiral") cae en
  "Candados" y conserva metadata.codigo_interno = "1-RK"
- las categorías-código (6-CL, 1-RK...) ya NO aparecen activas en /store/product-categories
- `git log --oneline -1` en develop
**No tocar:** idempotente; conservar el código interno como metadato (no borrarlo).
**Evidencia:** `reasignar-categorias-tipo.ts` exit 0: 22 categorías-tipo creadas, 608/608
productos reasignados (0 sin cruce), 14 categorías-código desactivadas. `verify-...ts`:
CL128 "Candado manguera espiral"→["Candados"], metadata.codigo_interno=1-RK; categorías
ACTIVAS=22 (solo tipos), códigos aún activos=[] (0). Re-ejecución probó idempotencia
("ya existían"/"ya estaban inactivas"). Commit 4bbbe3b en develop (pusheado).

## [done] 3. Storefront muestra las categorías nuevas + verificación
**Condición:** la navegación del storefront muestra las categorías de compra legibles
(no los códigos), accesibles para lector de pantalla, y al abrir una categoría lista
sus productos reales desde la Store API.
**Check (imprimir):**
- `cd src/storefront && npm run build` exit 0
- smoke a :8000: la navegación muestra nombres legibles (ej. "Bombas", "Cascos") y
  NINGÚN código tipo "6-CL" visible al cliente
- abrir una categoría (ej. "Candados") lista productos reales
- `npx @axe-core/cli http://localhost:8000` → 0 violaciones critical/serious
- `git log --oneline -1` en develop
**No tocar:** anti-alucinación; accesibilidad no se degrada; sin secretos.
**Evidencia:** `npm run build` exit 0 (tras `rm -rf .next` para limpiar fetch-cache viejo).
Smoke (`scripts/smoke-categorias-storefront.sh`, SMOKE OK): nav muestra las 22 categorías
legibles (Bombas/Cascos/Candados/Transmisión/...), 0 códigos como nombre de categoría;
/co/categories/candados HTTP 200 lista los candados reales. `npx @axe-core/cli` (Chrome-
for-Testing) → 0 violations. Storefront es data-driven (sin cambios de código). Commit
40539ba en develop (pusheado).

<!--
=================== FASE B — IMÁGENES DEL CATÁLOGO ===================
Fuente: /home/sadimus/Documentos/Fof/drive-download-20250611T144345Z-1-001/
680 imágenes por carpeta de categoría. Patrón de nombre:
"<Nombre> mod <ID> Precio<n> [(<variación>)].<ext>"
-> 629 cruzan por ID(+variación) con el SKU sembrado (cruce 100% verificado:
   557 IDs imágenes == 557 IDs CSV). Las 51 sin patrón = productos SIN_ID; sus
   nombres de archivo COINCIDEN con el title -> mapear por nombre+categoría.
Medusa: imágenes a nivel de PRODUCTO (galería + thumbnail).
=====================================================================
-->

## [done] 4. Mapeo imagen→producto (script + reporte)
**Condición:** un script recorre la carpeta drive-download, extrae de cada nombre el
`mod <ID>` y la `(variación)` (y para los 51 sin patrón, empareja por nombre+categoría
con el title del producto), y genera `data/imagenes_map.json` que asocia cada imagen
con un producto de Medusa. Reporte visible con la cobertura.
**Check (imprimir):**
- correr el script: imprime "mapeadas X/680" con X >= 646 (>=95%) y lista las NO mapeadas
- `data/imagenes_map.json` generado (ruta_imagen -> product_id/handle)
- `git log --oneline -1` en develop (script + json, NO las imágenes)
**No tocar:** el precio del nombre NO altera precios (anti-alucinación); no commitear
imágenes ni la carpeta drive-download.
**Evidencia:** `data/mapear_imagenes.py` → mapeadas 680/680 (100% ≥646): 629 por ID
(`mod <ID>`→product_id) + 51 por nombre+categoría (colores PITILLOS, coronillas con IDs
embebidos, manubrios 800mm...), 0 no mapeadas. 563 productos distintos con ≥1 imagen.
`data/imagenes_map.json` (ruta→product_id/handle/variación/match); CL128→su foto. Commit
1990c87 en develop (pusheado); imágenes y drive-download NO commiteados (gitignore).

## [done] 5. Subir imágenes a Medusa y anexarlas a los productos
**Condición:** según el mapeo, las imágenes se suben a Medusa (file module) y se
asignan a la galería de cada producto (todas las fotos de sus variaciones) con un
thumbnail principal. Re-ejecutable sin duplicar.
**Check (imprimir):**
- `npx medusa exec ./src/.../upload-images.ts` exit 0 e imprime "productos con imagen: N"
- query a Medusa: nº de productos con >=1 imagen >= 540 (de 608); y un producto conocido
  (CL128 "Candado manguera espiral") tiene imagen vía Admin API
- `git log --oneline -1` en develop (script + gitignore; NO binarios)
**No tocar:** idempotente (no duplicar al re-correr); gitignorear `static/` y la carpeta
drive-download; no commitear binarios.
**Evidencia:** `upload-images.ts` exit 0 → "productos con imagen: 608 | imágenes subidas:
680 | sin producto: 0"; re-corrida idempotente (saltados: 608, subidas: 0). `verify-
images.ts`: 608/608 con ≥1 imagen y thumbnail (≥540). Admin API: CL128 "Candado manguera
espiral" tiene 1 imagen; el archivo /static sirve HTTP 200 image/jpeg (5.1MB, base64 OK),
url→localhost:9001 (file-module configurado). Commit 6cf4613 en develop (pusheado);
static/ y drive-download gitignoreados (sin binarios al repo).

## [done] 6. Storefront muestra las imágenes + cierre del catálogo
**Condición:** el storefront muestra las imágenes reales: la página de un producto
conocido y el catálogo renderizan `<img>` con la foto subida (no placeholder), con la
navegación de categorías legibles de la Fase A ya activa.
**Check (imprimir):**
- `cd src/storefront && npm run build` exit 0
- `curl` a la página del producto CL128 trae `<img>` cuyo src apunta a la imagen del
  backend (no placeholder); el listado muestra thumbnails reales
- `npx @axe-core/cli http://localhost:8000` → 0 violaciones critical/serious
- `git log --oneline -1` en develop (commit pusheado)
**No tocar:** anti-alucinación; sin secretos; no romper categorías ni lo existente.
**Evidencia:** `npm run build` exit 0 (981 páginas, tras `rm -rf .next`). La página de CL128
(`/co/products/candado-manguera-espiral`, HTTP 200) renderiza `<img>` next/image apuntando
a `http://localhost:9001/static/...CL128...JPG` (no placeholder); el optimizer la sirve
HTTP 200 image/jpeg; el listado de Candados trae 68 thumbnails reales del backend. Smoke
catálogo completo: SMOKE OK. `npx @axe-core/cli` (Chrome-for-Testing) → 0 violations.
Categorías legibles de Fase A activas. Commit 4bf3432 en develop (pusheado).
