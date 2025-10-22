import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import fg from 'fast-glob';
import path from 'node:path';

function buildInputs() {
  // Build from HTML files so Vite emits HTML pages
  // Server utilities expect hashed *.html files in static/widgets
  // Note: paths are relative to root (src/)
  const files = fg.sync('**/index.html', { cwd: 'src', dot: false });
  return Object.fromEntries(
    files.map((f) => [path.basename(path.dirname(f)), path.resolve('src', f)])
  );
}

const inputs = buildInputs();

export default defineConfig({
  root: 'src',
  plugins: [
    tailwindcss(),
    react(),
  ],
  server: {
    port: 4445,
    strictPort: true,
    cors: true,
  },
  esbuild: {
    jsx: 'automatic',
    jsxImportSource: 'react',
    target: 'es2022',
  },
  build: {
    target: 'es2022',
    sourcemap: true,
    minify: 'esbuild',
    outDir: '../../server/static/widgets',
    emptyOutDir: true,
    assetsDir: '.',
    rollupOptions: {
      input: inputs,
      output: {
        entryFileNames: '[name]-[hash].js',
        chunkFileNames: '[name]-[hash].js',
        assetFileNames: '[name]-[hash].[ext]',
      },
      preserveEntrySignatures: 'strict',
    },
  },
  resolve: {
    alias: {
      // Ensure imports work correctly with new root
      '@': path.resolve(__dirname, './src'),
    },
  },
});
