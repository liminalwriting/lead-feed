import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Browser may open via 127.0.0.1 while Next reports localhost (or vice versa)
  allowedDevOrigins: ["127.0.0.1", "localhost"],
};

export default nextConfig;
