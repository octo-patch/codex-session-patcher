import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { NaiveUiResolver } from 'unplugin-vue-components/resolvers'

const backendHost = process.env.BACKEND_HOST || '127.0.0.1'
const backendPort = process.env.BACKEND_PORT || '8080'
const normalizedBackendHost =
  backendHost.includes(':') && !backendHost.startsWith('[') ? `[${backendHost}]` : backendHost

export default defineConfig({
  plugins: [
    vue(),
    Components({
      resolvers: [NaiveUiResolver()]
    })
  ],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: `http://${normalizedBackendHost}:${backendPort}`,
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  }
})
