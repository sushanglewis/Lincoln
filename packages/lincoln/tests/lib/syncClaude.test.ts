import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { syncClaudeCode } from '../../src/lib/syncClaude.js'

describe('syncClaudeCode', () => {
  let tmpDir: string
  let payloadRoot: string
  let targetDir: string

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lincoln-sync-test-'))
    payloadRoot = path.join(tmpDir, 'payload')
    targetDir = path.join(tmpDir, 'claude')

    fs.mkdirSync(path.join(payloadRoot, '.claude', 'agents'), { recursive: true })
    fs.writeFileSync(
      path.join(payloadRoot, '.claude', 'agents', 'default.md'),
      '# default agent\n'
    )
    fs.writeFileSync(
      path.join(payloadRoot, 'CLAUDE.md'),
      '# Lincoln\n'
    )
  })

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true })
  })

  it('copies agents directory', () => {
    const report = syncClaudeCode({
      payloadRoot,
      targetDir,
      version: '1.6.0',
      dryRun: false
    })
    expect(report.written).toContain('.claude/agents/default.md')
    expect(fs.existsSync(path.join(targetDir, 'agents', 'default.md'))).toBe(true)
  })

  it('merges CLAUDE.md managed block', () => {
    syncClaudeCode({ payloadRoot, targetDir, version: '1.6.0', dryRun: false })
    const claudeMd = fs.readFileSync(path.join(tmpDir, 'CLAUDE.md'), 'utf8')
    expect(claudeMd).toContain('<!-- lincoln:begin -->')
    expect(claudeMd).toContain('# Lincoln')
  })

  it('skips unchanged files in dry-run', () => {
    syncClaudeCode({ payloadRoot, targetDir, version: '1.6.0', dryRun: false })
    const report = syncClaudeCode({
      payloadRoot,
      targetDir,
      version: '1.6.0',
      dryRun: true
    })
    expect(report.skipped).toContain('.claude/agents/default.md')
    expect(report.written).toHaveLength(0)
  })
})
