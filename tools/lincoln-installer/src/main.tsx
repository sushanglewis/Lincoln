#!/usr/bin/env node
import { main } from './cli'

console.log(
  '⚠️  lincoln-install is deprecated. Run: npm install -g @sushanglewis/lincoln && lincoln install'
)

main().catch((err) => {
  console.error(err instanceof Error ? err.message : String(err))
  process.exit(1)
})
