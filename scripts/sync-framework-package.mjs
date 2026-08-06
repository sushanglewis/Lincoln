#!/usr/bin/env node
/**
 * Sync Lincoln framework runtime payload into packages/lincoln/framework/.
 *
 * This script mirrors the allowlist used by scripts/package-lincoln-plugin.py
 * so the npm package can bundle the same files that the release tarball uses.
 */

import crypto from 'node:crypto'
import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const ROOT = path.resolve(path.dirname(__filename), '..')
const PAYLOAD_DIR = path.join(ROOT, 'packages', 'lincoln', 'framework')
const VERSION_FILE = path.join(ROOT, '.version-bump.json')

const ALLOWLIST_DIRS = ['.claude', '.claude-plugin', 'scripts', 'tools']
const ALLOWLIST_FILES = [
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

const DENYLIST_NAMES = new Set([
  '.git',
  '.context',
  '.venv',
  'venv',
  'oss',
  '.pytest_cache',
  '__pycache__',
  '.DS_Store',
  'node_modules'
])
const DENYLIST_PREFIXES = ['issue-']
const SKIP_PATHS = new Set([
  '.claude/templates/issue-package',
  'tools/lincoln-installer/dist',
  'tools/lincoln-installer/node_modules',
  'tools/lincoln-installer/coverage'
])

async function loadVersion() {
  const raw = await fs.readFile(VERSION_FILE, 'utf8')
  const data = JSON.parse(raw)
  if (typeof data.version !== 'string') {
    throw new Error('.version-bump.json missing version string')
  }
  return data.version
}

function isDenied(relativePath) {
  const parts = relativePath.split(path.sep)
  for (const part of parts) {
    if (DENYLIST_NAMES.has(part)) return true
    for (const prefix of DENYLIST_PREFIXES) {
      if (part.startsWith(prefix)) return true
    }
  }
  for (const skip of SKIP_PATHS) {
    if (relativePath === skip || relativePath.startsWith(skip + path.sep)) {
      return true
    }
  }
  return false
}

async function* walk(dir, baseDir) {
  const entries = await fs.readdir(dir, { withFileTypes: true })
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name)
    const relativePath = path.relative(baseDir, fullPath)
    if (isDenied(relativePath)) continue
    if (entry.isDirectory()) {
      yield* walk(fullPath, baseDir)
    } else if (entry.isFile()) {
      yield { fullPath, relativePath }
    }
  }
}

async function sha256(filePath) {
  const data = await fs.readFile(filePath)
  return crypto.createHash('sha256').update(data).digest('hex')
}

async function syncPayload(version) {
  await fs.rm(PAYLOAD_DIR, { recursive: true, force: true })
  await fs.mkdir(PAYLOAD_DIR, { recursive: true })

  const copied = []

  for (const dir of ALLOWLIST_DIRS) {
    const src = path.join(ROOT, dir)
    try {
      await fs.access(src)
    } catch {
      continue
    }

    for await (const { fullPath, relativePath } of walk(src, ROOT)) {
      const dest = path.join(PAYLOAD_DIR, relativePath)
      await fs.mkdir(path.dirname(dest), { recursive: true })
      await fs.copyFile(fullPath, dest)
      copied.push(relativePath)
    }
  }

  for (const file of ALLOWLIST_FILES) {
    const src = path.join(ROOT, file)
    try {
      await fs.access(src)
    } catch {
      continue
    }
    const dest = path.join(PAYLOAD_DIR, file)
    await fs.mkdir(path.dirname(dest), { recursive: true })
    await fs.copyFile(src, dest)
    copied.push(file)
  }

  copied.sort()

  const manifestFiles = []
  for (const relativePath of copied) {
    const filePath = path.join(PAYLOAD_DIR, relativePath)
    manifestFiles.push({
      path: relativePath,
      sha256: await sha256(filePath)
    })
  }

  const manifest = {
    version,
    generatedAt: new Date().toISOString(),
    files: manifestFiles
  }

  await fs.writeFile(
    path.join(PAYLOAD_DIR, 'manifest.json'),
    JSON.stringify(manifest, null, 2) + '\n'
  )

  return copied
}

async function checkPayload(version) {
  try {
    await fs.access(PAYLOAD_DIR)
  } catch {
    return { ok: false, reason: 'framework payload directory missing' }
  }

  const manifestPath = path.join(PAYLOAD_DIR, 'manifest.json')
  let manifest
  try {
    const raw = await fs.readFile(manifestPath, 'utf8')
    manifest = JSON.parse(raw)
  } catch {
    return { ok: false, reason: 'manifest.json missing or unreadable' }
  }

  if (manifest.version !== version) {
    return { ok: false, reason: `version mismatch: ${manifest.version} != ${version}` }
  }

  for (const entry of manifest.files) {
    const filePath = path.join(PAYLOAD_DIR, entry.path)
    try {
      const actual = await sha256(filePath)
      if (actual !== entry.sha256) {
        return { ok: false, reason: `checksum mismatch: ${entry.path}` }
      }
    } catch {
      return { ok: false, reason: `missing file: ${entry.path}` }
    }
  }

  return { ok: true }
}

async function main() {
  const args = process.argv.slice(2)
  const version = await loadVersion()

  if (args.includes('--dump-allowlist')) {
    console.log(JSON.stringify({ dirs: ALLOWLIST_DIRS, files: ALLOWLIST_FILES }, null, 2))
    return 0
  }

  if (args.includes('--check')) {
    const result = await checkPayload(version)
    if (result.ok) {
      console.log(`framework payload up to date (${version})`)
      return 0
    }
    console.error(`framework payload out of sync: ${result.reason}`)
    return 1
  }

  const copied = await syncPayload(version)
  console.log(`synced ${copied.length} files to ${PAYLOAD_DIR} (${version})`)
  return 0
}

main().then((code) => process.exit(code)).catch((err) => {
  console.error(err)
  process.exit(1)
})
