import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    // Avoid esbuild pre-bundling issues by disabling discovery
    noDiscovery: true,
    include: [],
  },
  // Fully disable esbuild transforms to avoid Windows service crash
  esbuild: false,
  server: {
    host: true,
    hmr: { overlay: false },
  },
});
