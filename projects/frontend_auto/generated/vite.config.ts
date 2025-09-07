import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/core': path.resolve(__dirname, './src/core'),
      '@/app': path.resolve(__dirname, './src/app'),
      '@/providers': path.resolve(__dirname, './src/providers'),
      '@/services': path.resolve(__dirname, './src/services'),
      '@/hooks': path.resolve(__dirname, './src/hooks'),
      '@/components': path.resolve(__dirname, './src/components'),
      '@/features': path.resolve(__dirname, './src/features'),
      '@/utils': path.resolve(__dirname, './src/utils'),
      '@/constants': path.resolve(__dirname, './src/constants'),
      '@/styles': path.resolve(__dirname, './src/styles'),
      '@/pages': path.resolve(__dirname, './src/pages'),
      '@/mocks': path.resolve(__dirname, './src/mocks'),
      '@/plugins': path.resolve(__dirname, './src/plugins'),
      '@/workers': path.resolve(__dirname, './src/workers'),
    }
  },
  server: {
    port: 3000,
    open: true,
    cors: true
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('react')) {
              return 'react-vendor';
            }
            if (id.includes('@mui') || id.includes('@emotion')) {
              return 'ui-vendor';
            }
            return 'vendor';
          }
        }
      }
    }
  },
  worker: {
    format: 'es'
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom']
  }
})
