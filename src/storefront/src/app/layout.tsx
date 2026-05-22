import { getBaseURL } from "@lib/util/env"
import { Metadata } from "next"
import { Inter, Oswald } from "next/font/google"
import "styles/globals.css"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
})

const oswald = Oswald({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-oswald",
  display: "swap",
})

export const metadata: Metadata = {
  metadataBase: new URL(getBaseURL()),
}

export default function RootLayout(props: { children: React.ReactNode }) {
  return (
    <html
      lang="es"
      data-mode="light"
      className={`${inter.variable} ${oswald.variable}`}
    >
      <body className="font-sans antialiased text-brand-ink">
        <main className="relative">{props.children}</main>
      </body>
    </html>
  )
}
