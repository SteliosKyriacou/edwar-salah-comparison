import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq, req) => {
            const clientIp = req.socket.remoteAddress || ''
            // Convert ::ffff:1.2.3.4 to 1.2.3.4
            const clean = clientIp.replace(/^::ffff:/, '')
            proxyReq.setHeader('X-Forwarded-For', clean)
          })
        },
      },
      '/dashboard': {
        target: 'http://localhost:8000',
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq, req) => {
            const clientIp = req.socket.remoteAddress || ''
            const clean = clientIp.replace(/^::ffff:/, '')
            proxyReq.setHeader('X-Forwarded-For', clean)
          })
        },
      },
    },
  },
})
