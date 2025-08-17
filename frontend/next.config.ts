import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    // For Vercel deployment, use environment variable
    // For local development, fallback to production backend
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://209.38.142.207:8000';
    
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
