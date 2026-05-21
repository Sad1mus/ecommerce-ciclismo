import { Metadata } from "next"

import InteractiveLink from "@modules/common/components/interactive-link"

export const metadata: Metadata = {
  title: "404",
  description: "Algo salió mal",
}

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-64px)]">
      <h1 className="text-2xl-semi text-ui-fg-base">Página no encontrada</h1>
      <p className="text-small-regular text-ui-fg-base">
        El carrito al que intentaste acceder no existe. Borra tus cookies e
        inténtalo de nuevo.
      </p>
      <InteractiveLink href="/">Ir a la página de inicio</InteractiveLink>
    </div>
  )
}
