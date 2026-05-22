import LocalizedClientLink from "@modules/common/components/localized-client-link"

const Hero = () => {
  return (
    <div className="relative h-[78vh] min-h-[520px] w-full overflow-hidden bg-brand-ink">
      {/* Fondo deportivo: degradado oscuro + destellos de acento (decorativo) */}
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-gradient-to-br from-brand-ink via-brand-coal to-brand-steel"
      />
      <div
        aria-hidden="true"
        className="absolute -right-24 -top-24 h-[420px] w-[420px] rounded-full bg-brand-orange/25 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="absolute -left-20 bottom-0 h-[360px] w-[360px] rounded-full bg-brand-lime/10 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="absolute inset-x-0 bottom-0 h-1.5 bg-gradient-to-r from-brand-orange via-brand-lime to-brand-orange"
      />

      <div className="content-container relative z-10 flex h-full flex-col justify-center gap-6">
        <span className="accent-bar" />
        <p className="font-display uppercase tracking-[0.3em] text-brand-lime text-sm small:text-base">
          Ciclismo · MTB · Ruta
        </p>
        <h1 className="font-display font-bold uppercase leading-[0.95] text-white text-5xl small:text-7xl medium:text-8xl max-w-4xl">
          Domina <span className="text-brand-orange">cada</span> terreno
        </h1>
        <p className="max-w-xl text-base small:text-lg text-white/80">
          Componentes, accesorios y repuestos para tu bicicleta. Calidad de
          taller, precios en pesos colombianos y envío a todo el país.
        </p>
        <div className="mt-2 flex flex-col gap-3 xsmall:flex-row">
          <LocalizedClientLink href="/store" className="btn-accent">
            Explorar la tienda
          </LocalizedClientLink>
          <LocalizedClientLink
            href="/store"
            className="btn-outline-light"
          >
            Ver todos los productos
          </LocalizedClientLink>
        </div>
      </div>
    </div>
  )
}

export default Hero
