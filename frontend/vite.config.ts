import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath } from 'url'
import { defineConfig } from 'vite'

// https://vite.dev/config/
// Dev'da ildizdan (localhost:5173/teachers), build'da Django static yo'li ostidan xizmat qiladi.
export default defineConfig(({ command }) => ({
  base: command === 'serve' ? '/' : '/static/web/dist/',
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // QOLLANMA.md repo ildizida (frontend/ dan tashqarida) joylashgan
    fs: { allow: ['..'] },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    outDir: '../web/static/web/dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: 'assets/index-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },
  },
}))
