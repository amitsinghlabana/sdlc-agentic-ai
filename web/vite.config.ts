import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The built app is served by FastAPI from web/dist at the site root,
// so base "/" is correct. During `npm run dev`, /api is proxied to uvicorn.
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});

