import { fileURLToPath } from 'node:url';
import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
export default defineConfig({ plugins: [react(), tailwindcss()], base: process.env.VITE_BASE_PATH ?? '/', resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } }, test: { environment: 'jsdom', allowOnly: false, exclude: ['e2e/**', 'node_modules/**'] } });
