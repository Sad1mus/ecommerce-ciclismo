import { loadEnv, defineConfig } from '@medusajs/framework/utils'

loadEnv(process.env.NODE_ENV || 'development', process.cwd())

// URL pública del backend para servir los archivos subidos (static/).
// El provider local por defecto usa :9000 (incorrecto aquí), así que lo fijamos
// al backend real (:9001) para que el storefront cargue las imágenes.
const BACKEND_URL =
  process.env.MEDUSA_BACKEND_URL || `http://localhost:${process.env.PORT || 9001}`

module.exports = defineConfig({
  projectConfig: {
    databaseUrl: process.env.DATABASE_URL,
    http: {
      storeCors: process.env.STORE_CORS!,
      adminCors: process.env.ADMIN_CORS!,
      authCors: process.env.AUTH_CORS!,
      jwtSecret: process.env.JWT_SECRET || "supersecret",
      cookieSecret: process.env.COOKIE_SECRET || "supersecret",
    }
  },
  modules: [
    {
      resolve: "@medusajs/medusa/file",
      options: {
        providers: [
          {
            resolve: "@medusajs/medusa/file-local",
            id: "local",
            options: { backend_url: `${BACKEND_URL}/static` },
          },
        ],
      },
    },
  ],
})
