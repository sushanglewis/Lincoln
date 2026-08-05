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
    if (fs.existsSync(targetSettings)) {
      const existing = JSON.parse(fs.readFileSync(targetSettings, 'utf8'))
      merged = deepMergeSettings(existing, incoming)
    }

    const wouldChange =
      !fs.existsSync(targetSettings) ||
      JSON.stringify(merged) !== JSON.stringify(JSON.parse(fs.readFileSync(targetSettings, 'utf8')))

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
