import { describe, it, expect } from 'vitest'
import type { SyncReport } from '../../src/lib/syncClaude.js'
import { runHarnessAdapter } from '../../src/lib/runHarnessAdapter.js'
import { syncHarnesses } from '../../src/lib/syncHarness.js'
import type { LincolnPaths } from '../../src/lib/paths.js'
import type { HarnessId } from '../../src/lib/harnessDetect.js'

describe('runHarnessAdapter', () => {
  it('returns report on successful adapter run', async () => {
    const spawn = () => ({
      on(event: string, handler: (code: number | null) => void) {
        if (event === 'close') {
          handler(0)
        }
      },
      stdout: { on: () => {} },
      stderr: { on: () => {} }
    }) as unknown as import('node:child_process').ChildProcess

    const report = await runHarnessAdapter({
      harnessId: 'codex',
      payloadRoot: '/payload',
      projectDir: '/home/.lincoln/project',
      homeDir: '/home',
      pythonPath: '/venv/bin/python',
      dryRun: false,
      spawnCommand: spawn
    })

    expect(report.warnings).toHaveLength(0)
    expect(report.written).toContain('codex')
  })

  it('returns warning when adapter exits non-zero', async () => {
    const spawn = () => ({
      on(event: string, handler: (code: number | null) => void) {
        if (event === 'close') {
          handler(1)
        }
      },
      stdout: { on: () => {} },
      stderr: { on: () => {} }
    }) as unknown as import('node:child_process').ChildProcess

    const report = await runHarnessAdapter({
      harnessId: 'opencode',
      payloadRoot: '/payload',
      projectDir: '/home/.lincoln/project',
      homeDir: '/home',
      pythonPath: '/venv/bin/python',
      dryRun: false,
      spawnCommand: spawn
    })

    expect(report.warnings.length).toBeGreaterThan(0)
    expect(report.warnings[0]).toContain('opencode')
  })

  it('skips writes in dry-run mode', async () => {
    const spawn = () => {
      throw new Error('should not spawn in dry run')
    }

    const report = await runHarnessAdapter({
      harnessId: 'codex',
      payloadRoot: '/payload',
      projectDir: '/home/.lincoln/project',
      homeDir: '/home',
      pythonPath: '/venv/bin/python',
      dryRun: true,
      spawnCommand: spawn as unknown as typeof import('node:child_process').spawn
    })

    expect(report.written).toContain('codex (dry run)')
  })
})

describe('syncHarnesses', () => {
  const paths = {
    homeDir: '/home',
    lincolnHome: '/home/.lincoln',
    versionsDir: '/home/.lincoln/versions',
    currentDir: '/home/.lincoln/current',
    versionMarker: '/home/.lincoln/marker.json',
    venvDir: '/home/.lincoln/venv',
    claudeDir: '/home/.claude',
    codexDir: '/home/.codex',
    opencodeDir: '/home/.opencode'
  } satisfies LincolnPaths

  it('syncs claude-code using syncClaudeCode', async () => {
    const report: SyncReport = {
      written: ['claude.md'],
      skipped: [],
      preserved: [],
      warnings: [],
      settingsTouched: []
    }
    const result = await syncHarnesses({
      harnesses: ['claude-code'],
      payloadRoot: '/payload',
      paths,
      projectDir: '/home/.lincoln/project',
      version: '1.5.4',
      dryRun: false,
      syncClaude: () => report
    })

    expect(result['claude-code']).toBe(report)
  })

  it('returns warning for unsupported harness', async () => {
    const result = await syncHarnesses({
      harnesses: ['cursor' as HarnessId],
      payloadRoot: '/payload',
      paths,
      projectDir: '/home/.lincoln/project',
      version: '1.5.4',
      dryRun: false
    })

    expect(result['cursor'].warnings[0]).toContain('Unsupported')
  })
})
