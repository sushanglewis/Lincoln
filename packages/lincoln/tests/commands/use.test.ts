import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { use } from '../../src/commands/use.js'
import { resolveLincolnPaths } from '../../src/lib/paths.js'

describe('use', () => {
  let tmpDir: string

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lincoln-use-test-'))
  })

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true })
  })

  function seedVersion(version: string): string {
    const versionDir = path.join(tmpDir, '.lincoln', 'versions', version)
    fs.mkdirSync(versionDir, { recursive: true })
    fs.writeFileSync(path.join(versionDir, 'payload.txt'), `payload for ${version}`)
    return versionDir
  }

  function makeDeps(overrides: Record<string, unknown> = {}) {
    return {
      paths: resolveLincolnPaths(tmpDir),
      ensureVersionAvailable: async () => {},
      runInstall: async () => 0,
      ...overrides
    }
  }

  it('rejects invalid version strings', async () => {
    const code = await use('not a version!', { dryRun: false, yes: true }, makeDeps())
    expect(code).toBe(1)
  })

  it('accepts semver strings', async () => {
    seedVersion('1.6.0')
    const code = await use('1.6.0', { dryRun: true, yes: false }, makeDeps())
    expect(code).toBe(0)
  })

  it('accepts dist-tag strings', async () => {
    const code = await use('latest', { dryRun: true, yes: false }, makeDeps())
    expect(code).toBe(0)
  })

  it('returns 0 in dry-run mode without touching the filesystem', async () => {
    seedVersion('1.6.0')
    const currentDir = path.join(tmpDir, '.lincoln', 'current')
    const code = await use('1.6.0', { dryRun: true, yes: false }, makeDeps())
    expect(code).toBe(0)
    expect(fs.existsSync(currentDir)).toBe(false)
  })

  it('refuses to switch without --yes in non-dry-run mode', async () => {
    seedVersion('1.6.0')
    const code = await use('1.6.0', { dryRun: false, yes: false }, makeDeps())
    expect(code).toBe(1)
  })

  it('switches ~/.lincoln/current to an already-installed version', async () => {
    const versionDir = seedVersion('1.6.0')
    const code = await use('1.6.0', { dryRun: false, yes: true }, makeDeps())
    expect(code).toBe(0)

    const currentDir = path.join(tmpDir, '.lincoln', 'current')
    const stat = fs.lstatSync(currentDir)
    if (stat.isSymbolicLink()) {
      const target = fs.readlinkSync(currentDir)
      expect(path.resolve(path.dirname(currentDir), target)).toBe(versionDir)
    } else {
      // Fallback copy for filesystems without symlink support
      expect(stat.isDirectory()).toBe(true)
      expect(fs.existsSync(path.join(currentDir, 'payload.txt'))).toBe(true)
    }
  })

  it('replaces an existing current link when switching versions', async () => {
    const oldDir = seedVersion('1.5.0')
    const newDir = seedVersion('1.6.0')
    const currentDir = path.join(tmpDir, '.lincoln', 'current')
    fs.symlinkSync(oldDir, currentDir)

    const code = await use('1.6.0', { dryRun: false, yes: true }, makeDeps())
    expect(code).toBe(0)

    const stat = fs.lstatSync(currentDir)
    if (stat.isSymbolicLink()) {
      const target = fs.readlinkSync(currentDir)
      expect(path.resolve(path.dirname(currentDir), target)).toBe(newDir)
    } else {
      expect(fs.existsSync(path.join(currentDir, 'payload.txt'))).toBe(true)
      const content = fs.readFileSync(path.join(currentDir, 'payload.txt'), 'utf8')
      expect(content).toContain('1.6.0')
    }
  })

  it('provisions the version when it is not already installed', async () => {
    const calls: string[] = []
    const code = await use(
      '1.6.0',
      { dryRun: false, yes: true },
      makeDeps({
        ensureVersionAvailable: async (version: string) => {
          calls.push(version)
          seedVersion(version)
        }
      })
    )
    expect(code).toBe(0)
    expect(calls).toEqual(['1.6.0'])
  })

  it('returns 1 when provisioning fails', async () => {
    const code = await use(
      '9.9.9',
      { dryRun: false, yes: true },
      makeDeps({
        ensureVersionAvailable: async () => {
          throw new Error('version not found')
        }
      })
    )
    expect(code).toBe(1)
  })

  it('invokes lincoln install after switching versions', async () => {
    seedVersion('1.6.0')
    let installRan = false
    const code = await use(
      '1.6.0',
      { dryRun: false, yes: true },
      makeDeps({
        runInstall: async () => {
          installRan = true
          return 0
        }
      })
    )
    expect(code).toBe(0)
    expect(installRan).toBe(true)
  })

  it('returns 1 when lincoln install fails', async () => {
    seedVersion('1.6.0')
    const code = await use(
      '1.6.0',
      { dryRun: false, yes: true },
      makeDeps({
        runInstall: async () => 1
      })
    )
    expect(code).toBe(1)
  })
})
