import { defineConfig } from 'tsup'

export default defineConfig({
  entry: ['src/main.tsx'],
  outDir: 'dist',
  format: ['esm'],
  target: 'node20',
  platform: 'node',
  bundle: true,
  splitting: false,
  sourcemap: true,
  clean: true,
  dts: false,
  esbuildOptions(options) {
    options.jsx = 'automatic'
  },
})
