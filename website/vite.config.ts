import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// `npm run dev` serves the pages alone; `npm run preview` builds and runs them with the
// API (wrangler pages dev), which is what the dev proxy below points at.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy: { "/api": "http://127.0.0.1:8788" } },
});
