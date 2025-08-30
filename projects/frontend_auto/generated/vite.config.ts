import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react({
      // Enable React Fast Refresh
      fastRefresh: true,
      // Include .jsx and .tsx files
      include: "**/*.{jsx,tsx}",
    })
  ],
  
  // Path resolution
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@/core': resolve(__dirname, './src/core'),
      '@/app': resolve(__dirname, './src/app'),
      '@/components': resolve(__dirname, './src/components'),
      '@/pages': resolve(__dirname, './src/pages'),
      '@/providers': resolve(__dirname, './src/providers'),
      '@/services': resolve(__dirname, './src/services'),
      '@/store': resolve(__dirname, './src/store'),
      '@/hooks': resolve(__dirname, './src/hooks'),
      '@/utils': resolve(__dirname, './src/utils'),
      '@/data': resolve(__dirname, './src/data'),
      '@/styles': resolve(__dirname, './src/styles'),
    }
  },

  // Development server configuration
  server: {
    port: 3000,
    host: true,
    open: false,
    hmr: {
      overlay: true
    },
    // Proxy API calls to backend during development
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      }
    }
  },

  // Build configuration
  build: {
    target: 'esnext',
    outDir: 'dist',
    sourcemap: true,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      }
    },
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks for better caching
          react: ['react', 'react-dom'],
          motion: ['framer-motion'],
          spring: ['react-spring'],
          zustand: ['zustand'],
        }
      }
    },
    // Increase chunk size warning limit for game assets
    chunkSizeWarningLimit: 1000,
  },

  // Environment variables
  define: {
    // Expose build timestamp
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
    // Ensure process.env.NODE_ENV is available
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
  },

  // CSS configuration
  css: {
    postcss: './postcss.config.cjs',
    modules: {
      localsConvention: 'camelCaseOnly'
    }
  },

  // Optimize dependencies
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react/jsx-runtime',
      'framer-motion',
      'react-spring',
      'zustand',
      'zustand/middleware',
    ],
    exclude: ['@vite/client', '@vite/env']
  },

  // Preview server (for production builds)
  preview: {
    port: 4173,
    host: true,
  },

  // Base public path
  base: './',

  // Enable experimental features for better performance
  experimental: {
    renderBuiltUrl: (filename: string) => {
      return { runtime: `window.__assetsPath(${JSON.stringify(filename)})` }
    }
  }
})
```

// Self-check comments:
// ✓ Uses `@/` imports with proper path aliases configured
// ✓ Configured for React, TypeScript, and Tailwind CSS processing
// ✓ Includes HMR and fast refresh for development
// ✓ Sets up proxy for API and WebSocket connections
// ✓ Optimizes build output with proper chunking strategy
// ✓ Includes PostCSS configuration reference for Tailwind
// ✓ Enables source maps and proper minification
// ✓ Configures dev server on port 3000 as expected
// N/A No providers/hooks needed for build config
// N/A No DOM/localStorage interactions in build config