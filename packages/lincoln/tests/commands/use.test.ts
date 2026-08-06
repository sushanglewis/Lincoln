import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { use } from '../../src/commands/use.js'
import { resolveLincolnPaths } from '../../src/lib/paths.js'

describe('use', () => {
  let tmpDir: string

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lincoln-use-test-'))
  })

  afterEach(() => {
    vi.restoreAllMocks()
    fs.rmSync(tmpDir, { recursive: true, force: true })
  })

  function seedVersion(version: string): string {
    const versionDir = path.join(tmpDir, '.lincoln', 'versions', version)
    fs.mkdirSync(versionDir, { recursive: true })
    fs.writeFileSync(path.join(versionDir, 'payload.txt'), `payload for ${version}`)
    return versionDir
  }

  function currentDirPath(): string {
    return path.join(tmpDir, '.lincoln', 'current')
  }

  function expectCurrentPointsAt(versionDir: string): void {
    const currentDir = currentDirPath()
    const stat = fs.lstatSync(currentDir)
    if (stat.isSymbolicLink()) {
      const target = fs.readlinkSync(currentDir)
      expect(path.resolve(path.dirname(currentDir), target)).toBe(versionDir)
    } else {
      // Fallback copy for filesystems without symlink support
      expect(stat.isDirectory()).toBe(true)
      expect(fs.existsSync(path.join(currentDir, 'payload.txt'))).toBe(true)
    }
  }

  function makeDeps(overrides: Record<string, unknown> = {}) {
    return {
      paths: resolveLincolnPaths(tmpDir),
      resolveVersion: async (spec: string) => spec.replace(/^v(?=\d)/, ''),
      ensureVersionAvailable: async () => {},
      npmGlobalRoot: async () => undefined as string | undefined,
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
    const code = await use('1.6.0', { dryRun: true, yes: false }, makeDeps())
    expect(code).toBe(0)
    expect(fs.existsSync(currentDirPath())).toBe(false)
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
    expectCurrentPointsAt(versionDir)
  })

  it('normalizes a v-prefixed version before switching', async () => {
    const versionDir = seedVersion('1.6.0')
    const code = await use('v1.6.0', { dryRun: false, yes: true }, makeDeps())
    expect(code).toBe(0)
    expectCurrentPointsAt(versionDir)
  })

  it('resolves dist-tags through the injected resolver', async () => {
    const versionDir = seedVersion('2.0.0-beta.1')
    const code = await use(
      'next',
      { dryRun: false, yes: true },
      makeDeps({
        resolveVersion: async (spec: string) => (spec === 'next' ? '2.0.0-beta.1' : spec)
      })
    )
    expect(code).toBe(0)
    expectCurrentPointsAt(versionDir)
  })

  it('returns 1 when version resolution fails', async () => {
    const code = await use(
      'nope',
      { dryRun: false, yes: true },
      makeDeps({
        resolveVersion: async () => {
          throw new Error('unknown dist-tag')
        }
      })
    )
    expect(code).toBe(1)
    expect(fs.existsSync(currentDirPath())).toBe(false)
  })

  it('replaces an existing current link when switching versions', async () => {
    const oldDir = seedVersion('1.5.0')
    const newDir = seedVersion('1.6.0')
    fs.symlinkSync(oldDir, currentDirPath())

    const code = await use('1.6.0', { dryRun: false, yes: true }, makeDeps())
    expect(code).toBe(0)

    const stat = fs.lstatSync(currentDirPath())
    if (stat.isSymbolicLink()) {
      const target = fs.readlinkSync(currentDirPath())
      expect(path.resolve(path.dirname(currentDirPath()), target)).toBe(newDir)
    } else {
      const content = fs.readFileSync(path.join(currentDirPath(), 'payload.txt'), 'utf8')
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

  it('copies the payload from the npm global root when provisioning leaves the version dir absent', async () => {
    const globalRoot = path.join(tmpDir, 'npm-global')
    const packageRoot = path.join(globalRoot, '@sushanglewis', 'lincoln')
    fs.mkdirSync(packageRoot, { recursive: true })
    fs.writeFileSync(path.join(packageRoot, 'payload.txt'), 'global payload for 1.6.0')

    const logSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    const code = await use(
      '1.6.0',
      { dryRun: false, yes: true },
      makeDeps({
        npmGlobalRoot: async () => globalRoot
      })
    )

    expect(code).toBe(0)
    const versionDir = path.join(tmpDir, '.lincoln', 'versions', '1.6.0')
    expect(fs.readFileSync(path.join(versionDir, 'payload.txt'), 'utf8')).toBe(
      'global payload for 1.6.0'
    )
    expectCurrentPointsAt(versionDir)
    expect(logSpy).toHaveBeenCalledWith('Switched Lincoln to 1.6.0')
  })

  it('fails loudly when provisioning leaves the version dir absent', async () => {
    const logSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    const code = await use(
      '1.6.0',
      { dryRun: false, yes: true },
      makeDeps({
        // ensureVersionAvailable "succeeds" but never populates the version
        // dir, and no npm global package is available to copy from.
        npmGlobalRoot: async () => undefined
      })
    )

    expect(code).toBe(1)
    expect(logSpy).not.toHaveBeenCalledWith(expect.stringContaining('Switched'))
    expect(errorSpy).toHaveBeenCalledWith(expect.stringContaining('did not produce'))
    expect(fs.existsSync(currentDirPath())).toBe(false)
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

  it('keeps current on the requested version even when install re-points it', async () => {
    const versionDir = seedVersion('1.6.0')
    const otherDir = seedVersion('9.9.9')
    const code = await use(
      '1.6.0',
      { dryRun: false, yes: true },
      makeDeps({
        runInstall: async () => {
          // Mirrors install.ts: it links current at the running CLI's own
          // version dir. `use` must re-assert the requested version.
          fs.rmSync(currentDirPath(), { recursive: true, force: true })
          fs.symlinkSync(otherDir, currentDirPath())
          return 0
        }
      })
    )
    expect(code).toBe(0)
    expectCurrentPointsAt(versionDir)
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
