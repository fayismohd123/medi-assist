import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      },
      '/start-recording': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      },
      '/stop-recording': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      },
      '/generate_report': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      },
      '/download-report': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  }
})
