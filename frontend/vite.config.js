import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 8790,
    host: '127.0.0.1',
    strictPort: true,
  },
  preview: {
    port: 8790,
    host: '127.0.0.1',
    strictPort: true,
  }
});
