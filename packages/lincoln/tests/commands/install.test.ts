import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { install, resolvePythonForVenv } from '../../src/commands/install.js'
import { resolveLincolnPaths } from '../../src/lib/paths.js'

describe('install', () => {
  let tmpDir: string

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lincoln-install-test-'))
  })

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true })
  })

  it('refuses to install without --yes in non-dry-run', async () => {
    const deps = {
      paths: resolveLincolnPaths(tmpDir),
      payloadRoot: path.join(tmpDir, '.lincoln', 'current'),
      syncClaude: () => ({ written: [], skipped: [], preserved: [], warnings: [], settingsTouched: [] })
    }
    const code = await install(
      { yes: false, dryRun: false, force: false, harnesses: ['claude-code'], noVenv: true },
      deps
    )
    expect(code).toBe(1)
  })

  it('succeeds in dry-run without --yes', async () => {
    fs.mkdirSync(path.join(tmpDir, '.claude'), { recursive: true })
    fs.mkdirSync(path.join(tmpDir, '.lincoln', 'current', '.claude', 'agents'), { recursive: true })
    fs.writeFileSync(
      path.join(tmpDir, '.lincoln', 'current', '.claude', 'agents', 'default.md'),
      '# agent\n'
    )

    const deps = {
      paths: resolveLincolnPaths(tmpDir),
      payloadRoot: path.join(tmpDir, '.lincoln', 'current'),
      syncClaude: () => ({ written: [], skipped: [], preserved: [], warnings: [], settingsTouched: [] })
    }
    const code = await install(
      { yes: false, dryRun: true, force: false, harnesses: [], noVenv: true },
      deps
    )
    expect(code).toBe(0)
  })
})

describe('resolvePythonForVenv', () => {
  it('returns env override when it is sufficient', async () => {
    const python = await resolvePythonForVenv('/custom/python3.11', [], async (cmd) =>
      cmd === '/custom/python3.11' ? 'Python 3.11.0' : undefined
    )
    expect(python).toBe('/custom/python3.11')
  })

  it('returns the first candidate whose version is sufficient', async () => {
    const python = await resolvePythonForVenv(undefined, ['python3.9', 'python3.10', 'python3.11'], async (cmd) => {
      if (cmd === 'python3.9') return 'Python 3.9.0'
      if (cmd === 'python3.10') return 'Python 3.10.0'
      if (cmd === 'python3.11') return 'Python 3.11.0'
      return undefined
    })
    expect(python).toBe('python3.10')
  })

  it('returns undefined when no candidate is sufficient', async () => {
    const python = await resolvePythonForVenv(undefined, ['python3.8', 'python3.9'], async (cmd) => cmd.includes('3.8') ? 'Python 3.8.0' : 'Python 3.9.0'
    )
    expect(python).toBeUndefined()
  })
})
