/** @type {import('next').NextConfig} */
const BACKEND = process.env.BACKEND_URL || "http://localhost:8004";

const nextConfig = {
  reactStrictMode: true,
  // Proxy API + market routes to the Python backend so the browser talks same-origin
  // (no CORS dependency in the happy path). Change BACKEND_URL to point elsewhere.
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${BACKEND}/api/:path*` },
      { source: "/market/:path*", destination: `${BACKEND}/market/:path*` },
    ];
  },
};

export default nextConfig;
