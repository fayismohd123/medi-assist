import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        credentials: 'include'
      },
      '/start-recording': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        credentials: 'include'
      },
      '/stop-recording': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        credentials: 'include'
      },
      '/generate_report': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        credentials: 'include'
      }
    }
  }
})
