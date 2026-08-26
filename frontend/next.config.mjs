/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/backend-api/:path*",
        destination: `${process.env.INTERNAL_API_URL || "http://localhost:28000"}/:path*`,
      },
    ];
  },
};

export default nextConfig;
