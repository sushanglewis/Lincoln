import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { install } from '../../src/commands/install.js'
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
