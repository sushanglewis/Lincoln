#!/usr/bin/env node
import { updateMain } from './update'

console.log(
  '⚠️  lincoln-update is deprecated. Run: npm install -g @sushanglewis/lincoln && lincoln install'
)

updateMain().catch((err) => {
  console.error(err instanceof Error ? err.message : String(err))
  process.exit(1)
})
