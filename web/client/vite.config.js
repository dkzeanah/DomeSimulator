import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// In development the React app runs on 5173 and hands /api to the Express
// server on 8787, so the browser sees one origin and the session cookie works.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': 'http://localhost:8787' },
  },
});
