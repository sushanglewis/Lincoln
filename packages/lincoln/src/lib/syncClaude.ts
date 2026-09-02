import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'
import { mergeManagedBlock } from './claudeMdMerge.js'

export interface SyncOptions {
  payloadRoot: string
  targetDir: string
  version: string
  dryRun: boolean
}

export interface SyncReport {
  written: string[]
  skipped: string[]
  preserved: string[]
  warnings: string[]
  settingsTouched?: string[]
}

export interface ClaudeHookCommand {
  type: 'command'
  command: string
  timeout?: number
}

export interface ClaudeHookEntry {
  matcher?: string
  lincoln?: boolean
  hooks: ClaudeHookCommand[]
}

export type ClaudeHooksMap = Record<string, ClaudeHookEntry[]>

const COPY_SUBDIRS = [
  'agents',
  'skills',
  'workflows',
  'stages',
  'schemas',
  'templates',
  'harnesses'
]

function sha256(filePath: string): string {
  const data = fs.readFileSync(filePath)
  return crypto.createHash('sha256').update(data).digest('hex')
}

function sameContent(a: string, b: string): boolean {
  return sha256(a) === sha256(b)
}

function deepMergeSettings(existing: unknown, incoming: unknown): unknown {
  if (Array.isArray(existing) && Array.isArray(incoming)) {
    return incoming
  }
  if (
    typeof existing === 'object' &&
    existing !== null &&
    typeof incoming === 'object' &&
    incoming !== null
  ) {
    const result: Record<string, unknown> = { ...existing }
    for (const [key, value] of Object.entries(incoming)) {
      if (key in result) {
        result[key] = deepMergeSettings(result[key], value)
      } else {
        result[key] = value
      }
    }
    return result
  }
  return incoming
}

export function syncClaudeCode(opts: SyncOptions): SyncReport {
  const report: SyncReport = {
    written: [],
    skipped: [],
    preserved: [],
    warnings: [],
    settingsTouched: []
  }

  const payloadClaude = path.join(opts.payloadRoot, '.claude')
  if (!fs.existsSync(payloadClaude)) {
    report.warnings.push(`payload .claude directory not found: ${payloadClaude}`)
    return report
  }

  if (!opts.dryRun) {
    fs.mkdirSync(opts.targetDir, { recursive: true })
  }

  for (const subdir of COPY_SUBDIRS) {
    const srcDir = path.join(payloadClaude, subdir)
    if (!fs.existsSync(srcDir)) {
      continue
    }

    const destDir = path.join(opts.targetDir, subdir)
    if (!opts.dryRun) {
      fs.mkdirSync(destDir, { recursive: true })
    }

    for (const entry of walkSync(srcDir)) {
      const relativePath = path.relative(srcDir, entry)
      const srcFile = entry
      const destFile = path.join(destDir, relativePath)

      if (fs.existsSync(destFile) && sameContent(srcFile, destFile)) {
        report.skipped.push(path.join('.claude', subdir, relativePath))
        continue
      }

      if (!opts.dryRun) {
        fs.mkdirSync(path.dirname(destFile), { recursive: true })
        fs.copyFileSync(srcFile, destFile)
      }
      report.written.push(path.join('.claude', subdir, relativePath))
    }
  }

  // settings.json merge
  const payloadSettings = path.join(payloadClaude, 'settings.json')
  const targetSettings = path.join(opts.targetDir, 'settings.json')
  if (fs.existsSync(payloadSettings)) {
    const incoming = JSON.parse(fs.readFileSync(payloadSettings, 'utf8'))
    let merged = incoming
    const existing = fs.existsSync(targetSettings)
      ? JSON.parse(fs.readFileSync(targetSettings, 'utf8'))
      : undefined
    if (existing !== undefined) {
      merged = deepMergeSettings(existing, incoming)
      if (typeof merged === 'object' && merged !== null) {
        const mergedObj = merged as Record<string, unknown>
        if (
          (typeof existing === 'object' && existing !== null && 'hooks' in existing) ||
          'hooks' in incoming
        ) {
          const existingHooks =
            typeof existing === 'object' && existing !== null
              ? (existing as Record<string, unknown>).hooks
              : undefined
          mergedObj.hooks = mergeHooks(existingHooks, incoming.hooks)
        }
      }
    }

    const wouldChange =
      existing === undefined ||
      JSON.stringify(merged) !== JSON.stringify(existing)

    if (wouldChange) {
      if (!opts.dryRun) {
        fs.writeFileSync(targetSettings, JSON.stringify(merged, null, 2) + '\n')
      }
      report.written.push('.claude/settings.json')
      report.settingsTouched = ['.claude/settings.json']
    } else {
      report.skipped.push('.claude/settings.json')
    }
  }

  // CLAUDE.md merge
  const payloadClaudeMd = path.join(opts.payloadRoot, 'CLAUDE.md')
  const targetClaudeMd = path.join(path.dirname(opts.targetDir), 'CLAUDE.md')
  if (fs.existsSync(payloadClaudeMd)) {
    const incomingBlock = fs.readFileSync(payloadClaudeMd, 'utf8')
    const existing = fs.existsSync(targetClaudeMd)
      ? fs.readFileSync(targetClaudeMd, 'utf8')
      : undefined
    const merged = mergeManagedBlock(existing, incomingBlock)

    if (merged !== existing) {
      if (!opts.dryRun) {
        fs.writeFileSync(targetClaudeMd, merged)
      }
      report.written.push('CLAUDE.md')
    } else {
      report.skipped.push('CLAUDE.md')
    }
  }

  return report
}

const LINCOLN_HOOK_FILES = new Set([
  'on-session-start.sh',
  'pre-tool-use.sh',
  'post-tool-use.sh',
  'on-stop.sh'
])

export function isLincolnHookCommand(command: string): boolean {
  if (command.includes('${CLAUDE_PLUGIN_ROOT}/.claude/hooks/')) {
    return true
  }
  for (const file of LINCOLN_HOOK_FILES) {
    if (command.includes(`/.claude/hooks/${file}`)) {
      return true
    }
  }
  return false
}

function isHookEntryLincoln(entry: ClaudeHookEntry): boolean {
  if (entry.lincoln === true) {
    return true
  }
  return entry.hooks.some((h) => h.type === 'command' && isLincolnHookCommand(h.command))
}

function normalizeHookEntry(value: unknown): ClaudeHookEntry | undefined {
  if (typeof value !== 'object' || value === null) {
    return undefined
  }
  const obj = value as Record<string, unknown>
  const hooks: ClaudeHookCommand[] = []
  if (Array.isArray(obj.hooks)) {
    for (const h of obj.hooks) {
      if (typeof h === 'object' && h !== null) {
        const hc = h as Record<string, unknown>
        if (hc.type === 'command' && typeof hc.command === 'string') {
          hooks.push({
            type: 'command',
            command: hc.command,
            timeout: typeof hc.timeout === 'number' ? hc.timeout : undefined
          })
        }
      }
    }
  }
  if (hooks.length === 0) {
    return undefined
  }
  const entry: ClaudeHookEntry = { hooks }
  if (typeof obj.matcher === 'string') {
    entry.matcher = obj.matcher
  }
  if (obj.lincoln === true) {
    entry.lincoln = true
  }
  return entry
}

function normalizeLegacyHookValue(value: unknown): ClaudeHookEntry[] | undefined {
  if (typeof value === 'string') {
    return [
      {
        hooks: [{ type: 'command', command: toStableHookCommand(value) }]
      }
    ]
  }
  if (Array.isArray(value)) {
    const entries: ClaudeHookEntry[] = []
    for (const item of value) {
      const entry = normalizeHookEntry(item)
      if (entry) {
        entries.push(entry)
      }
    }
    return entries.length > 0 ? entries : undefined
  }
  return undefined
}

function toStableHookCommand(command: string): string {
  if (command.startsWith('.claude/hooks/')) {
    return command.replace(/^\.claude\/hooks\//, '${CLAUDE_PLUGIN_ROOT}/.claude/hooks/')
  }
  if (command.startsWith('${CLAUDE_PLUGIN_ROOT}/.claude/hooks/')) {
    return command
  }
  return command
}

function normalizeHooksMap(value: unknown): ClaudeHooksMap {
  const result: ClaudeHooksMap = {}
  if (typeof value !== 'object' || value === null) {
    return result
  }
  for (const [eventName, eventValue] of Object.entries(value as Record<string, unknown>)) {
    const entries = normalizeLegacyHookValue(eventValue)
    if (entries) {
      result[eventName] = entries
    }
  }
  return result
}

export function mergeHooks(existing: unknown, incoming: unknown): ClaudeHooksMap {
  const existingMap = normalizeHooksMap(existing)
  const incomingMap = normalizeHooksMap(incoming)
  const result: ClaudeHooksMap = { ...existingMap }

  for (const [eventName, incomingEntries] of Object.entries(incomingMap)) {
    const existingEntries = result[eventName] ?? []
    const preserved: ClaudeHookEntry[] = []
    for (const entry of existingEntries) {
      if (!isHookEntryLincoln(entry)) {
        preserved.push(entry)
      }
    }
    result[eventName] = [...preserved, ...incomingEntries]
  }

  return result
}

function* walkSync(dir: string): Generator<string> {
  const entries = fs.readdirSync(dir, { withFileTypes: true })
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      yield* walkSync(fullPath)
    } else {
      yield fullPath
    }
  }
}
