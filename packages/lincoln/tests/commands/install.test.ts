import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { install, resolvePythonForVenv } from '../../src/commands/install.js'
import { resolveLincolnPaths } from '../../src/lib/paths.js'
import type { HarnessSyncReport } from '../../src/lib/syncHarness.js'

function makePrompt(selection: string[]) {
  return {
    confirm: async () => true,
    multiSelect: async () => selection,
    close: () => {}
  }
}

function emptySyncReport(): HarnessSyncReport {
  return {
    'claude-code': {
      written: [],
      skipped: [],
      preserved: [],
      warnings: []
    }
  }
}

describe('install', () => {
  let tmpDir: string

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lincoln-install-test-'))
  })

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true })
  })

  it('refuses to install without --yes in non-interactive mode', async () => {
    const deps = {
      paths: resolveLincolnPaths(tmpDir),
      payloadRoot: path.join(tmpDir, '.lincoln', 'current'),
      syncHarnesses: async () => emptySyncReport(),
      createPrompt: () => makePrompt([]),
      resolvePythonForVenv: async () => undefined,
      isTTY: false
    }
    const code = await install(
      { yes: false, dryRun: false, force: false, harnesses: ['claude-code'], noVenv: true, noInteractive: false },
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
      syncHarnesses: async () => emptySyncReport(),
      createPrompt: () => makePrompt([]),
      resolvePythonForVenv: async () => undefined,
      isTTY: false
    }
    const code = await install(
      { yes: false, dryRun: true, force: false, harnesses: [], noVenv: true, noInteractive: false },
      deps
    )
    expect(code).toBe(0)
  })

  it('uses selected harnesses in interactive mode', async () => {
    fs.mkdirSync(path.join(tmpDir, '.claude'), { recursive: true })
    fs.mkdirSync(path.join(tmpDir, '.lincoln', 'current', '.claude', 'agents'), { recursive: true })
    fs.writeFileSync(
      path.join(tmpDir, '.lincoln', 'current', '.claude', 'agents', 'default.md'),
      '# agent\n'
    )

    const syncHarnesses = async () => emptySyncReport()
    const deps = {
      paths: resolveLincolnPaths(tmpDir),
      payloadRoot: path.join(tmpDir, '.lincoln', 'current'),
      syncHarnesses,
      createPrompt: () => makePrompt(['claude-code']),
      resolvePythonForVenv: async () => undefined,
      isTTY: true
    }
    const code = await install(
      { yes: false, dryRun: false, force: false, harnesses: [], noVenv: true, noInteractive: false },
      deps
    )
    expect(code).toBe(0)
  })

  it('aborts when interactive selection is empty', async () => {
    fs.mkdirSync(path.join(tmpDir, '.claude'), { recursive: true })
    fs.mkdirSync(path.join(tmpDir, '.lincoln', 'current', '.claude', 'agents'), { recursive: true })
    fs.writeFileSync(
      path.join(tmpDir, '.lincoln', 'current', '.claude', 'agents', 'default.md'),
      '# agent\n'
    )

    const deps = {
      paths: resolveLincolnPaths(tmpDir),
      payloadRoot: path.join(tmpDir, '.lincoln', 'current'),
      syncHarnesses: async () => emptySyncReport(),
      createPrompt: () => makePrompt([]),
      resolvePythonForVenv: async () => undefined,
      isTTY: true
    }
    const code = await install(
      { yes: false, dryRun: false, force: false, harnesses: [], noVenv: true, noInteractive: false },
      deps
    )
    expect(code).toBe(1)
  })

  it('rejects unknown harness ids from --harnesses flag', async () => {
    fs.mkdirSync(path.join(tmpDir, '.lincoln', 'current', '.claude', 'agents'), { recursive: true })
    fs.writeFileSync(
      path.join(tmpDir, '.lincoln', 'current', '.claude', 'agents', 'default.md'),
      '# agent\n'
    )

    const deps = {
      paths: resolveLincolnPaths(tmpDir),
      payloadRoot: path.join(tmpDir, '.lincoln', 'current'),
      syncHarnesses: async () => emptySyncReport(),
      createPrompt: () => makePrompt([]),
      resolvePythonForVenv: async () => undefined,
      isTTY: false
    }
    const code = await install(
      { yes: true, dryRun: false, force: false, harnesses: ['cursor'], noVenv: true, noInteractive: false },
      deps
    )
    expect(code).toBe(1)
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
    const python = await resolvePythonForVenv(undefined, ['python3.8', 'python3.9'], async (cmd) =>
      cmd.includes('3.8') ? 'Python 3.8.0' : 'Python 3.9.0'
    )
    expect(python).toBeUndefined()
  })
})
