import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'

// Mirrors scripts/package-lincoln-plugin.py and scripts/sync-framework-package.mjs
export const FRAMEWORK_ALLOWLIST_DIRS = ['.claude', '.claude-plugin', 'scripts', 'tools']
export const FRAMEWORK_ALLOWLIST_FILES = [
  'README.md',
  'README.en.md',
  'USAGE.md',
  'CONTRIBUTING.md',
  'CLAUDE.md',
  'LICENSE',
  'RELEASE.md',
  '.version-bump.json',
  'requirements.txt',
  'SKILL.md'
]
export const FRAMEWORK_DENYLIST_NAMES = new Set([
  '.git',
  '.context',
  '.venv',
  'venv',
  'dist',
  'oss',
  '.pytest_cache',
  '__pycache__',
  '.DS_Store',
  'node_modules'
])
export const FRAMEWORK_DENYLIST_PREFIXES = ['issue-']
export const FRAMEWORK_SKIP_PATHS = new Set([
  '.claude/templates/issue-package',
  'tools/lincoln-installer/dist',
  'tools/lincoln-installer/node_modules',
  'tools/lincoln-installer/coverage'
])

function sha256(filePath: string): string {
  return crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex')
}

function isDenied(relativePath: string): boolean {
  const parts = relativePath.split(path.sep)
  for (const part of parts) {
    if (FRAMEWORK_DENYLIST_NAMES.has(part)) return true
    for (const prefix of FRAMEWORK_DENYLIST_PREFIXES) {
      if (part.startsWith(prefix)) return true
    }
  }
  for (const skip of FRAMEWORK_SKIP_PATHS) {
    if (relativePath === skip || relativePath.startsWith(skip + path.sep)) return true
  }
  return false
}

function isAllowlisted(relativePath: string): boolean {
  if (FRAMEWORK_ALLOWLIST_FILES.includes(relativePath)) return true
  for (const dir of FRAMEWORK_ALLOWLIST_DIRS) {
    if (relativePath === dir || relativePath.startsWith(dir + path.sep)) return true
  }
  return false
}

function isPreservedDir(relativePath: string): boolean {
  const normalized = relativePath.replace(/\\/g, '/')
  if (normalized === '.context' || normalized.startsWith('.context/')) return true
  const parts = normalized.split('/')
  for (const part of parts) {
    if (part.startsWith('issue-')) return true
  }
  return false
}

function isPreserved(relativePath: string): boolean {
  const normalized = relativePath.replace(/\\/g, '/')
  if (normalized === '.github/openspec-config.yml') return true
  return isPreservedDir(relativePath)
}

export interface VendoredFileReport {
  removable: string[]
  modified: string[]
  preserved: string[]
}

export function listVendoredFrameworkFiles(
  payloadRoot: string,
  projectRoot: string
): VendoredFileReport {
  const report: VendoredFileReport = { removable: [], modified: [], preserved: [] }

  function walk(dir: string): void {
    const entries = fs.readdirSync(dir, { withFileTypes: true })
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name)
      const relativePath = path.relative(projectRoot, fullPath)

      if (entry.isDirectory()) {
        if (isPreservedDir(relativePath)) {
          walk(fullPath)
        } else if (!isDenied(relativePath)) {
          walk(fullPath)
        }
        continue
      }

      if (isPreserved(relativePath)) {
        report.preserved.push(relativePath)
        continue
      }

      if (isDenied(relativePath)) continue
      if (!isAllowlisted(relativePath)) continue

      const payloadFile = path.join(payloadRoot, relativePath)
      if (!fs.existsSync(payloadFile)) {
        report.modified.push(relativePath)
        continue
      }

      if (sha256(fullPath) === sha256(payloadFile)) {
        report.removable.push(relativePath)
      } else {
        report.modified.push(relativePath)
      }
    }
  }

  if (fs.existsSync(projectRoot)) {
    walk(projectRoot)
  }

  return report
}
