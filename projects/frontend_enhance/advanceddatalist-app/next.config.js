/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['example.com'],
    // support next-gen formats
    deviceSizes: [320, 640, 1024, 1440, 1920],
  },
  // Enable server components flag in Next.js 13+ if you plan server components
  experimental: {
    appDir: true,
    serverActions: true,
  },
  env: {
    NEXT_PUBLIC_WS_ENDPOINT: process.env.NEXT_PUBLIC_WS_ENDPOINT,
  },
}