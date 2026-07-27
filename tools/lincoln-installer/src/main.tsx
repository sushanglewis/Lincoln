#!/usr/bin/env node
import { main } from './cli'

main().catch((err) => {
  console.error(err instanceof Error ? err.message : String(err))
  process.exit(1)
})
