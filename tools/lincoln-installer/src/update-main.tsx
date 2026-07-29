#!/usr/bin/env node
import { updateMain } from './update'

updateMain().catch((err) => {
  console.error(err instanceof Error ? err.message : String(err))
  process.exit(1)
})
