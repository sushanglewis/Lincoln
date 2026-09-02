import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { mergeHooks, type ClaudeHooksMap } from '../lib/syncClaude.js'

export interface HooksOptions {
  subcommand: 'install' | 'uninstall' | 'status'
  dryRun: boolean
  yes: boolean
}

export interface HooksDeps {
  homeDir: string
  lincolnHome: string
  claudeDir: string
  readFile: (filePath: string) => string
  writeFile: (filePath: string, content: string) => void
  mkdir: (dirPath: string) => void
  exists: (filePath: string) => boolean
}

export function createDefaultDeps(): HooksDeps {
  const homeDir = os.homedir()
  const lincolnHome = process.env.LINCOLN_HOME
    ? path.resolve(process.env.LINCOLN_HOME)
    : path.join(homeDir, '.lincoln')
  return {
    homeDir,
    lincolnHome,
    claudeDir: path.join(homeDir, '.claude'),
    readFile: (filePath) => fs.readFileSync(filePath, 'utf8'),
    writeFile: (filePath, content) => fs.writeFileSync(filePath, content),
    mkdir: (dirPath) => fs.mkdirSync(dirPath, { recursive: true }),
    exists: (filePath) => fs.existsSync(filePath)
  }
}

function readSettings(settingsPath: string, deps: HooksDeps): Record<string, unknown> {
  if (!deps.exists(settingsPath)) {
    return {}
  }
  try {
    const content = deps.readFile(settingsPath)
    return JSON.parse(content) as Record<string, unknown>
  } catch (err) {
    throw new Error(
      `Failed to parse ${settingsPath}: ${err instanceof Error ? err.message : String(err)}`
    )
  }
}

function loadPayloadHooks(deps: HooksDeps): { hooks: ClaudeHooksMap; error?: string } {
  const payloadSettings = path.join(deps.lincolnHome, 'current', '.claude', 'settings.json')
  if (!deps.exists(payloadSettings)) {
    return {
      hooks: {},
      error: `Lincoln payload not found at ${payloadSettings}. Run "lincoln install" first.`
    }
  }
  const payload = readSettings(payloadSettings, deps)
  const hooks = payload.hooks
  if (hooks === undefined) {
    return {
      hooks: {},
      error: `No hooks declared in Lincoln payload ${payloadSettings}`
    }
  }
  return { hooks: mergeHooks(undefined, hooks) }
}

function reportHooksChanges(
  before: Record<string, unknown>,
  after: Record<string, unknown>
): { added: string[]; changed: string[]; unchanged: string[] } {
  const beforeHooks = (before.hooks ?? {}) as Record<string, unknown>
  const afterHooks = (after.hooks ?? {}) as Record<string, unknown>
  const added: string[] = []
  const changed: string[] = []
  const unchanged: string[] = []

  for (const eventName of Object.keys(afterHooks)) {
    if (!(eventName in beforeHooks)) {
      added.push(eventName)
    } else if (JSON.stringify(beforeHooks[eventName]) !== JSON.stringify(afterHooks[eventName])) {
      changed.push(eventName)
    } else {
      unchanged.push(eventName)
    }
  }

  return { added, changed, unchanged }
}

export async function hooksInstall(
  options: HooksOptions,
  deps: HooksDeps = createDefaultDeps()
): Promise<number> {
  if (options.subcommand !== 'install') {
    console.error(`Unsupported hooks subcommand: ${options.subcommand}`)
    return 1
  }

  const settingsPath = path.join(deps.claudeDir, 'settings.json')
  const payload = loadPayloadHooks(deps)
  if (payload.error) {
    console.error(payload.error)
    return 1
  }

  const existingSettings = readSettings(settingsPath, deps)
  const mergedSettings = { ...existingSettings }
  mergedSettings.hooks = mergeHooks(existingSettings.hooks, payload.hooks)

  const { added, changed, unchanged } = reportHooksChanges(existingSettings, mergedSettings)
  const hasChanges = added.length > 0 || changed.length > 0

  if (!hasChanges) {
    console.log('Lincoln hooks are already up to date in ~/.claude/settings.json')
    return 0
  }

  if (!options.yes && !options.dryRun) {
    console.error(
      'This will modify ~/.claude/settings.json. Run with --yes to proceed, or use --dry-run to preview.'
    )
    return 1
  }

  if (options.dryRun) {
    console.log('Dry run: would update Lincoln hooks in ~/.claude/settings.json')
    if (added.length > 0) console.log(`  add: ${added.join(', ')}`)
    if (changed.length > 0) console.log(`  update: ${changed.join(', ')}`)
    if (unchanged.length > 0) console.log(`  unchanged: ${unchanged.join(', ')}`)
    return 0
  }

  deps.mkdir(deps.claudeDir)
  const tempPath = `${settingsPath}.tmp`
  deps.writeFile(tempPath, JSON.stringify(mergedSettings, null, 2) + '\n')
  fs.renameSync(tempPath, settingsPath)

  console.log('Updated Lincoln hooks in ~/.claude/settings.json')
  if (added.length > 0) console.log(`  add: ${added.join(', ')}`)
  if (changed.length > 0) console.log(`  update: ${changed.join(', ')}`)
  if (unchanged.length > 0) console.log(`  unchanged: ${unchanged.join(', ')}`)
  return 0
}
