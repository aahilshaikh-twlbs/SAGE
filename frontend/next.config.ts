import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://209.38.142.207:8000/:path*',
      },
    ];
  },
};

export default nextConfig;
