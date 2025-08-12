import type { NextConfig } from "next";

const backendUrl = process.env.BACKEND_URL || 'http://209.38.142.207:8000';

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'deuqpmn4rs7j5.cloudfront.net',
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: '*.cloudfront.net',
        port: '',
        pathname: '/**',
      },
    ],
  },

};

export default nextConfig;
