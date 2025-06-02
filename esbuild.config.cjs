const { build } = require('esbuild');
const path = require('path');

build({
  entryPoints: ['apps/web/src/engine/cli-runner.ts'],
  bundle: true,
  platform: 'node',
  format: 'cjs',
  outfile: 'execution_runner.cjs',
  external: ['node-fetch'],
  alias: {
    '@': path.resolve(__dirname, 'apps/web/src')
  },
  sourcemap: false,
  minify: false,
  target: 'node22',
  logLevel: 'info',
}).catch(() => process.exit(1));