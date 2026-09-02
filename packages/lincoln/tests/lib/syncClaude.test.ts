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
    fs.writeFileSync(
      path.join(payloadRoot, '.claude', 'settings.json'),
      JSON.stringify(
        {
          hooks: {
            SessionStart: [
              {
                hooks: [
                  {
                    type: 'command',
                    command: '${CLAUDE_PLUGIN_ROOT}/.claude/hooks/on-session-start.sh',
                    timeout: 60
                  }
                ]
              }
            ],
            PreToolUse: [
              {
                hooks: [
                  {
                    type: 'command',
                    command: '${CLAUDE_PLUGIN_ROOT}/.claude/hooks/pre-tool-use.sh',
                    timeout: 5
                  }
                ]
              }
            ],
            PostToolUse: [
              {
                hooks: [
                  {
                    type: 'command',
                    command: '${CLAUDE_PLUGIN_ROOT}/.claude/hooks/post-tool-use.sh',
                    timeout: 10
                  }
                ]
              }
            ],
            Stop: [
              {
                hooks: [
                  {
                    type: 'command',
                    command: '${CLAUDE_PLUGIN_ROOT}/.claude/hooks/on-stop.sh',
                    timeout: 10
                  }
                ]
              }
            ]
          }
        },
        null,
        2
      )
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
    expect(report.skipped).toContain('.claude/settings.json')
    expect(report.written).toHaveLength(0)
  })

  it('writes hooks in the Claude array-of-objects schema', () => {
    syncClaudeCode({ payloadRoot, targetDir, version: '1.6.0', dryRun: false })
    const settings = JSON.parse(fs.readFileSync(path.join(targetDir, 'settings.json'), 'utf8'))
    expect(settings.hooks.SessionStart).toEqual([
      {
        hooks: [
          {
            type: 'command',
            command: '${CLAUDE_PLUGIN_ROOT}/.claude/hooks/on-session-start.sh',
            timeout: 60
          }
        ]
      }
    ])
    expect(settings.hooks.PreToolUse).toEqual([
      {
        hooks: [
          {
            type: 'command',
            command: '${CLAUDE_PLUGIN_ROOT}/.claude/hooks/pre-tool-use.sh',
            timeout: 5
          }
        ]
      }
    ])
    expect(settings.hooks.PostToolUse).toEqual([
      {
        hooks: [
          {
            type: 'command',
            command: '${CLAUDE_PLUGIN_ROOT}/.claude/hooks/post-tool-use.sh',
            timeout: 10
          }
        ]
      }
    ])
    expect(settings.hooks.Stop).toEqual([
      {
        hooks: [
          {
            type: 'command',
            command: '${CLAUDE_PLUGIN_ROOT}/.claude/hooks/on-stop.sh',
            timeout: 10
          }
        ]
      }
    ])
  })

  it('preserves existing non-Lincoln hooks when merging', () => {
    fs.mkdirSync(targetDir, { recursive: true })
    fs.writeFileSync(
      path.join(targetDir, 'settings.json'),
      JSON.stringify(
        {
          hooks: {
            SessionStart: [
              {
                hooks: [
                  {
                    type: 'command',
                    command: '/usr/local/bin/my-custom-start.sh',
                    timeout: 30
                  }
                ]
              }
            ]
          }
        },
        null,
        2
      )
    )

    syncClaudeCode({ payloadRoot, targetDir, version: '1.6.0', dryRun: false })
    const settings = JSON.parse(fs.readFileSync(path.join(targetDir, 'settings.json'), 'utf8'))
    expect(settings.hooks.SessionStart).toHaveLength(2)
    expect(settings.hooks.SessionStart[0].hooks[0].command).toBe('/usr/local/bin/my-custom-start.sh')
    expect(settings.hooks.SessionStart[1].hooks[0].command).toBe(
      '${CLAUDE_PLUGIN_ROOT}/.claude/hooks/on-session-start.sh'
    )
  })

  it('replaces existing Lincoln hooks while preserving user hooks', () => {
    fs.mkdirSync(targetDir, { recursive: true })
    fs.writeFileSync(
      path.join(targetDir, 'settings.json'),
      JSON.stringify(
        {
          hooks: {
            SessionStart: [
              {
                hooks: [
                  {
                    type: 'command',
                    command: '/usr/local/bin/my-custom-start.sh',
                    timeout: 30
                  }
                ]
              },
              {
                hooks: [
                  {
                    type: 'command',
                    command: '${CLAUDE_PLUGIN_ROOT}/.claude/hooks/on-session-start.sh',
                    timeout: 120
                  }
                ]
              }
            ]
          }
        },
        null,
        2
      )
    )

    syncClaudeCode({ payloadRoot, targetDir, version: '1.6.0', dryRun: false })
    const settings = JSON.parse(fs.readFileSync(path.join(targetDir, 'settings.json'), 'utf8'))
    expect(settings.hooks.SessionStart).toHaveLength(2)
    expect(settings.hooks.SessionStart[0].hooks[0].command).toBe('/usr/local/bin/my-custom-start.sh')
    expect(settings.hooks.SessionStart[1].hooks[0].timeout).toBe(60)
  })

  it('migrates legacy string-form Lincoln hooks to array-of-objects', () => {
    fs.mkdirSync(targetDir, { recursive: true })
    fs.writeFileSync(
      path.join(targetDir, 'settings.json'),
      JSON.stringify(
        {
          hooks: {
            SessionStart: '.claude/hooks/on-session-start.sh',
            PreToolUse: '.claude/hooks/pre-tool-use.sh',
            PostToolUse: '.claude/hooks/post-tool-use.sh',
            Stop: '.claude/hooks/on-stop.sh'
          }
        },
        null,
        2
      )
    )

    syncClaudeCode({ payloadRoot, targetDir, version: '1.6.0', dryRun: false })
    const settings = JSON.parse(fs.readFileSync(path.join(targetDir, 'settings.json'), 'utf8'))
    expect(Array.isArray(settings.hooks.SessionStart)).toBe(true)
    expect(settings.hooks.SessionStart[0].hooks[0].type).toBe('command')
    expect(settings.hooks.SessionStart[0].hooks[0].command).toBe(
      '${CLAUDE_PLUGIN_ROOT}/.claude/hooks/on-session-start.sh'
    )
    expect(settings.hooks.SessionStart[0].hooks[0].timeout).toBe(60)
  })

  it('is idempotent on re-install', () => {
    syncClaudeCode({ payloadRoot, targetDir, version: '1.6.0', dryRun: false })
    const firstRun = JSON.parse(fs.readFileSync(path.join(targetDir, 'settings.json'), 'utf8'))
    const secondReport = syncClaudeCode({
      payloadRoot,
      targetDir,
      version: '1.6.0',
      dryRun: false
    })
    const secondRun = JSON.parse(fs.readFileSync(path.join(targetDir, 'settings.json'), 'utf8'))
    expect(secondReport.skipped).toContain('.claude/settings.json')
    expect(secondRun).toEqual(firstRun)
  })
})
