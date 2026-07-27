import { existsSync, statSync } from 'node:fs'
import { resolve } from 'node:path'

import type { ParsedArgs } from './args'

export interface InstallerConfig {
  root: string
  harnesses: string[]
  yes: boolean
  dryRun: boolean
  format: 'human' | 'json'
}

export function resolveConfig(args: ParsedArgs): InstallerConfig {
  const root = resolve(args.root)
  if (!existsSync(root) || !statSync(root).isDirectory()) {
    throw new Error(`Project root does not exist or is not a directory: ${root}`)
  }
  const setupScript = resolve(root, 'scripts', 'lincoln-setup.py')
  if (!existsSync(setupScript)) {
    throw new Error(
      `Lincoln setup script not found at ${setupScript}. ` +
        `Run lincoln-install inside a Lincoln project checkout.`
    )
  }
  return {
    root,
    harnesses: args.harness.length > 0 ? args.harness : [],
    yes: args.yes,
    dryRun: args.dryRun,
    format: args.format,
  }
}
