import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  experimental: {
    serverActions: {
      allowedOrigins: ["localhost:3000"],
    },
  },
  turbopack: {
    // Explicitly set the workspace root to this project directory
    // to silence the "multiple lockfiles detected" warning
    root: __dirname,
  },
  async rewrites() {
    // Proxy /api/* to the FastAPI backend in development
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
