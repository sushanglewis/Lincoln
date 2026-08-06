import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { update } from '../../src/commands/update.js'
import { resolveLincolnPaths } from '../../src/lib/paths.js'

describe('update', () => {
  let tmpDir: string

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lincoln-update-test-'))
  })

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true })
  })

  function makeDeps(overrides: Record<string, unknown> = {}) {
    return {
      paths: resolveLincolnPaths(tmpDir),
      latestVersion: async () => '1.6.0',
      currentVersion: () => '1.5.0',
      npmInstallGlobal: async () => 0,
      runInstall: async () => 0,
      ...overrides
    }
  }

  it('returns 0 when already up to date', async () => {
    const code = await update(
      { check: true, dryRun: true, yes: true },
      makeDeps({
        currentVersion: () => '1.6.0',
        latestVersion: async () => '1.6.0'
      })
    )
    expect(code).toBe(0)
  })

  it('returns 0 in check mode without invoking npm install or sync', async () => {
    let installCalled = false
    let syncCalled = false
    const code = await update(
      { check: true, dryRun: false, yes: false },
      makeDeps({
        npmInstallGlobal: async () => {
          installCalled = true
          return 0
        },
        runInstall: async () => {
          syncCalled = true
          return 0
        }
      })
    )
    expect(code).toBe(0)
    expect(installCalled).toBe(false)
    expect(syncCalled).toBe(false)
  })

  it('returns 0 in dry-run mode without invoking npm install or sync', async () => {
    let installCalled = false
    let syncCalled = false
    const code = await update(
      { check: false, dryRun: true, yes: false },
      makeDeps({
        npmInstallGlobal: async () => {
          installCalled = true
          return 0
        },
        runInstall: async () => {
          syncCalled = true
          return 0
        }
      })
    )
    expect(code).toBe(0)
    expect(installCalled).toBe(false)
    expect(syncCalled).toBe(false)
  })

  it('refuses to update without --yes in non-dry-run mode', async () => {
    const code = await update(
      { check: false, dryRun: false, yes: false },
      makeDeps()
    )
    expect(code).toBe(1)
  })

  it('invokes npm install and lincoln install when updating', async () => {
    const calls: string[] = []
    const code = await update(
      { check: false, dryRun: false, yes: true },
      makeDeps({
        npmInstallGlobal: async (version: string) => {
          calls.push(`npm:${version}`)
          return 0
        },
        runInstall: async () => {
          calls.push('install')
          return 0
        }
      })
    )
    expect(code).toBe(0)
    expect(calls).toEqual(['npm:1.6.0', 'install'])
  })

  it('passes yes=true to lincoln install after update', async () => {
    let capturedOptions: { yes?: boolean } | undefined
    const code = await update(
      { check: false, dryRun: false, yes: true },
      makeDeps({
        runInstall: async (options: { yes?: boolean }) => {
          capturedOptions = options
          return 0
        }
      })
    )
    expect(code).toBe(0)
    expect(capturedOptions?.yes).toBe(true)
  })

  it('returns 1 when npm install fails', async () => {
    let syncCalled = false
    const code = await update(
      { check: false, dryRun: false, yes: true },
      makeDeps({
        npmInstallGlobal: async () => 1,
        runInstall: async () => {
          syncCalled = true
          return 0
        }
      })
    )
    expect(code).toBe(1)
    expect(syncCalled).toBe(false)
  })

  it('returns 1 when lincoln install fails after npm install', async () => {
    const code = await update(
      { check: false, dryRun: false, yes: true },
      makeDeps({
        runInstall: async () => 1
      })
    )
    expect(code).toBe(1)
  })

  it('returns 1 when the registry query fails', async () => {
    const code = await update(
      { check: false, dryRun: false, yes: true },
      makeDeps({
        latestVersion: async () => {
          throw new Error('network unreachable')
        }
      })
    )
    expect(code).toBe(1)
  })

  it('does not downgrade when the installed version is ahead of latest', async () => {
    let installCalled = false
    let syncCalled = false
    const code = await update(
      { check: false, dryRun: false, yes: true },
      makeDeps({
        currentVersion: () => '2.0.0-beta.1',
        latestVersion: async () => '1.6.0',
        npmInstallGlobal: async () => {
          installCalled = true
          return 0
        },
        runInstall: async () => {
          syncCalled = true
          return 0
        }
      })
    )
    expect(code).toBe(0)
    expect(installCalled).toBe(false)
    expect(syncCalled).toBe(false)
  })
})
