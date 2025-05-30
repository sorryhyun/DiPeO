import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import * as path from 'path';

export default defineConfig({
  build: {
    reportCompressedSize: true,
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        manualChunks: {
          // Core React dependencies
          'react-vendor': ['react', 'react-dom', 'react/jsx-runtime'],
          
          // Large diagram library
          'diagram-vendor': ['@xyflow/react'],
          
          // UI libraries
          'ui-vendor': ['@repo/ui-kit', 'sonner', 'react-resizable-panels'],
          
          // Icon library
          'icon-vendor': ['lucide-react'],
          
          // Store libraries
          'store-vendor': ['zustand'],
          
          // Large components - lazy loaded
          'conversation': ['./src/features/layout/components/ConversationDashboard'],
          'properties': ['./src/features/properties/components/PropertiesRenderer'],
          'modals': ['./src/features/layout/components/modals/ApiKeysModal'],
        },
        
        // Better chunk naming
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId
            ? chunkInfo.facadeModuleId.split('/').pop()?.replace('.tsx', '').replace('.ts', '') || 'chunk'
            : 'chunk';
          return `assets/${facadeModuleId}-[hash].js`;
        },
        
        // Optimize asset names
        assetFileNames: 'assets/[name]-[hash].[ext]',
        entryFileNames: 'assets/[name]-[hash].js',
      },
      
      // External dependencies to reduce bundle size
      external: (_id) => {
        // Don't bundle these in production if they're CDN available
        return false; // Keep all dependencies bundled for now
      },
    },
    
    // Enable better tree shaking
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info'],
      },
      mangle: {
        safari10: true,
      },
    },
    
    // Optimize chunks
    chunkSizeWarningLimit: 1000,
    target: ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari14'],
  },
  plugins: [
    react(),
  ],
  preview: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        // Ensure streaming responses are flushed immediately
        configure: (proxy, _options) => {
          proxy.on('proxyRes', (_proxyRes, _req, res) => {
            if (typeof res.flushHeaders === 'function') {
              res.flushHeaders();
            }
          });
        }
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        // Ensure streaming responses are flushed immediately
        configure: (proxy, _options) => {
          proxy.on('proxyRes', (_proxyRes, _req, res) => {
            if (typeof res.flushHeaders === 'function') {
              res.flushHeaders();
            }
          });
        }
      },
    },
  }
});