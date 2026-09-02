import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { hooksInstall } from '../../src/commands/hooks.js'

function makeDeps(tmpDir: string) {
  return {
    homeDir: tmpDir,
    lincolnHome: path.join(tmpDir, '.lincoln'),
    claudeDir: path.join(tmpDir, '.claude'),
    readFile: (filePath: string) => fs.readFileSync(filePath, 'utf8'),
    writeFile: (filePath: string, content: string) => fs.writeFileSync(filePath, content),
    mkdir: (dirPath: string) => fs.mkdirSync(dirPath, { recursive: true }),
    exists: (filePath: string) => fs.existsSync(filePath)
  }
}

function writePayloadSettings(tmpDir: string) {
  const payloadSettings = path.join(tmpDir, '.lincoln', 'current', '.claude', 'settings.json')
  fs.mkdirSync(path.dirname(payloadSettings), { recursive: true })
  fs.writeFileSync(
    payloadSettings,
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
}

describe('hooks install', () => {
  let tmpDir: string

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lincoln-hooks-test-'))
  })

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true })
  })

  it('writes hooks when no settings file exists', async () => {
    writePayloadSettings(tmpDir)
    const deps = makeDeps(tmpDir)
    const code = await hooksInstall({ subcommand: 'install', dryRun: false, yes: true }, deps)
    expect(code).toBe(0)

    const settings = JSON.parse(fs.readFileSync(path.join(tmpDir, '.claude', 'settings.json'), 'utf8'))
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
  })

  it('preserves existing non-Lincoln hooks', async () => {
    writePayloadSettings(tmpDir)
    const deps = makeDeps(tmpDir)
    fs.mkdirSync(deps.claudeDir, { recursive: true })
    fs.writeFileSync(
      path.join(deps.claudeDir, 'settings.json'),
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

    const code = await hooksInstall({ subcommand: 'install', dryRun: false, yes: true }, deps)
    expect(code).toBe(0)

    const settings = JSON.parse(fs.readFileSync(path.join(deps.claudeDir, 'settings.json'), 'utf8'))
    expect(settings.hooks.SessionStart).toHaveLength(2)
    expect(settings.hooks.SessionStart[0].hooks[0].command).toBe('/usr/local/bin/my-custom-start.sh')
    expect(settings.hooks.SessionStart[1].hooks[0].command).toBe(
      '${CLAUDE_PLUGIN_ROOT}/.claude/hooks/on-session-start.sh'
    )
  })

  it('requires --yes without --dry-run', async () => {
    writePayloadSettings(tmpDir)
    const deps = makeDeps(tmpDir)
    const code = await hooksInstall({ subcommand: 'install', dryRun: false, yes: false }, deps)
    expect(code).toBe(1)
    expect(fs.existsSync(path.join(deps.claudeDir, 'settings.json'))).toBe(false)
  })

  it('does not write in dry-run mode', async () => {
    writePayloadSettings(tmpDir)
    const deps = makeDeps(tmpDir)
    const code = await hooksInstall({ subcommand: 'install', dryRun: true, yes: false }, deps)
    expect(code).toBe(0)
    expect(fs.existsSync(path.join(deps.claudeDir, 'settings.json'))).toBe(false)
  })

  it('is idempotent on second run', async () => {
    writePayloadSettings(tmpDir)
    const deps = makeDeps(tmpDir)
    await hooksInstall({ subcommand: 'install', dryRun: false, yes: true }, deps)
    const firstRun = JSON.parse(fs.readFileSync(path.join(deps.claudeDir, 'settings.json'), 'utf8'))

    const code = await hooksInstall({ subcommand: 'install', dryRun: false, yes: true }, deps)
    expect(code).toBe(0)
    const secondRun = JSON.parse(fs.readFileSync(path.join(deps.claudeDir, 'settings.json'), 'utf8'))
    expect(secondRun).toEqual(firstRun)
  })

  it('reports unsupported subcommands', async () => {
    writePayloadSettings(tmpDir)
    const deps = makeDeps(tmpDir)
    const code = await hooksInstall({ subcommand: 'status', dryRun: false, yes: true }, deps)
    expect(code).toBe(1)
  })

  it('fails when payload settings.json is missing', async () => {
    const deps = makeDeps(tmpDir)
    const code = await hooksInstall({ subcommand: 'install', dryRun: false, yes: true }, deps)
    expect(code).toBe(1)
  })
})
