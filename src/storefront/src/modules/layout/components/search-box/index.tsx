"use client"

import { useParams, useRouter } from "next/navigation"
import { useState } from "react"
import { MagnifyingGlass } from "@medusajs/icons"

const SearchBox = () => {
  const router = useRouter()
  const { countryCode } = useParams() as { countryCode?: string }
  const [value, setValue] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const query = value.trim()
    if (!query) return
    const cc = countryCode || "co"
    router.push(`/${cc}/search?q=${encodeURIComponent(query)}`)
  }

  return (
    <form
      onSubmit={handleSubmit}
      role="search"
      className="flex items-center gap-2 rounded-rounded border border-white/25 bg-white/5 px-3 py-1.5 focus-within:border-brand-orange transition-colors"
    >
      <label htmlFor="nav-search-input" className="sr-only">
        Buscar productos
      </label>
      <input
        id="nav-search-input"
        type="search"
        name="q"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Buscar productos…"
        autoComplete="off"
        className="bg-transparent text-white placeholder:text-white/50 outline-none text-small-regular w-32 medium:w-48"
        data-testid="nav-search-input"
      />
      <button
        type="submit"
        aria-label="Buscar"
        className="text-white/80 hover:text-brand-orange transition-colors"
        data-testid="nav-search-button"
      >
        <MagnifyingGlass />
      </button>
    </form>
  )
}

export default SearchBox
