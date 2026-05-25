import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],

  server: {
    port: 3100,
    open: true,
  },

  preview: {
    host: '0.0.0.0',
    port: Number(process.env.PORT) || 4273,
  },
});
