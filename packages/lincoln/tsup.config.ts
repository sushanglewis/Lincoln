import { defineConfig } from 'tsup'

export default defineConfig({
  entry: ['src/main.ts', 'src/postinstall.ts'],
  outDir: 'dist',
  format: ['esm'],
  target: 'node20',
  splitting: false,
  sourcemap: true,
  clean: true,
  dts: true,
  banner: {
    js: '#!/usr/bin/env node'
  }
})
