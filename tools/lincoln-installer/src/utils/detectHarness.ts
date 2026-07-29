import { existsSync } from 'node:fs'
import { homedir } from 'node:os'
import { join } from 'node:path'

import type { HarnessInfo } from '../types'

const HARNESS_DEFINITIONS: Omit<HarnessInfo, 'installed'>[] = [
  {
    id: 'claude-code',
    name: 'Claude Code',
    description: 'Anthropic Claude Code agent',
    projectDir: '.claude',
  },
  {
    id: 'cursor',
    name: 'Cursor',
    description: 'Cursor editor rules',
    projectDir: '.cursor',
  },
  {
    id: 'codex',
    name: 'Codex',
    description: 'OpenAI Codex CLI',
    projectDir: '.codex',
  },
  {
    id: 'opencode',
    name: 'OpenCode',
    description: 'OpenCode agent',
    projectDir: '.opencode',
  },
]

function globalDirFor(id: string, homeDir: string): string | undefined {
  if (id === 'cursor') return undefined
  return join(homeDir, '.' + id.replace('claude-code', 'claude'))
}

export function detectHarnesses(root: string, homeDir: string = homedir()): HarnessInfo[] {
  return HARNESS_DEFINITIONS.map((harness) => {
    const projectInstalled = harness.projectDir
      ? existsSync(join(root, harness.projectDir))
      : false
    const global = globalDirFor(harness.id, homeDir)
    const globalInstalled = global ? existsSync(global) : false
    return {
      ...harness,
      installed: projectInstalled || globalInstalled,
    }
  })
}
