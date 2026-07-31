import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { resolve, join } from 'node:path'
import { describe, expect, test, afterEach } from 'vitest'
import { resolveConfig } from '../../src/config/resolveConfig'
import type { ParsedArgs } from '../../src/config/args'

function makeProjectDir(): string {
  const root = mkdtempSync(join(tmpdir(), 'lincoln-'))
  const scriptsDir = join(root, 'scripts')
  mkdirSync(scriptsDir)
  writeFileSync(join(scriptsDir, 'lincoln-setup.py'), '')
  return root
}

function makeArgs(overrides: Partial<ParsedArgs> = {}, root = makeProjectDir()): ParsedArgs {
  return {
    root,
    harness: [],
    yes: false,
    dryRun: false,
    noTui: false,
    format: 'human',
    help: false,
    ...overrides,
  }
}

describe('resolveConfig', () => {
  const dirs: string[] = []

  afterEach(() => {
    for (const dir of dirs) {
      rmSync(dir, { recursive: true, force: true })
    }
    dirs.length = 0
  })

  test('resolves root to absolute path', () => {
    const root = makeProjectDir()
    dirs.push(root)
    const config = resolveConfig(makeArgs({ root }))
    expect(config.root).toBe(resolve(root))
  })

  test('uses provided harnesses', () => {
    const root = makeProjectDir()
    dirs.push(root)
    const config = resolveConfig(makeArgs({ root, harness: ['claude-code'] }))
    expect(config.harnesses).toEqual(['claude-code'])
  })

  test('passes boolean flags through', () => {
    const root = makeProjectDir()
    dirs.push(root)
    const config = resolveConfig(makeArgs({ root, yes: true, dryRun: true, format: 'json' }))
    expect(config.yes).toBe(true)
    expect(config.dryRun).toBe(true)
    expect(config.format).toBe('json')
  })

  test('throws when root does not exist', () => {
    expect(() => resolveConfig(makeArgs({ root: '/does/not/exist' }, '/does/not/exist'))).toThrow(
      'Project root does not exist or is not a directory'
    )
  })

  test('throws when setup script is missing', () => {
    const root = mkdtempSync(join(tmpdir(), 'lincoln-'))
    dirs.push(root)
    expect(() => resolveConfig(makeArgs({ root }, root))).toThrow(
      'Lincoln setup script not found'
    )
  })
})
