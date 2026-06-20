import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const repositoryName = process.env.GITHUB_REPOSITORY?.split("/")[1];
  const base = mode === "production" && repositoryName ? `/${repositoryName}/` : "/";

  return {
    base,
    plugins: [react()],
    optimizeDeps: {
      noDiscovery: true,
      include: [],
    },
    server: {
      proxy: {
        "/api": "http://127.0.0.1:8000",
      },
    },
  };
});
