/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Salida lean para Docker (server minimo + estaticos).
  output: "standalone",
};

export default nextConfig;
