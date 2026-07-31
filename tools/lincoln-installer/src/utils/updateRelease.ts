import { createWriteStream } from 'node:fs'
import {
  copyFileSync,
  existsSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  rmSync,
} from 'node:fs'
import { dirname, join, relative, resolve, sep } from 'node:path'
import { extract, ReadEntry } from 'tar'

export interface ReleaseInfo {
  version: string
  assetUrl: string
  publishedAt: string
  checksumUrl?: string
}

export interface MergeResult {
  updated: string[]
  preserved: string[]
  backupDir: string
}

export interface UpdateOptions {
  root: string
  repo?: string
  dryRun?: boolean
}

export interface UpdateResult {
  success: boolean
  fromVersion?: string
  toVersion?: string
  updated: string[]
  preserved: string[]
  backupDir?: string
  error?: string
}

const GITHUB_API_BASE = 'https://api.github.com/repos'
const DEFAULT_REPO = 'sushanglewis/Lincoln'
const FETCH_TIMEOUT_MS = 15_000
const DOWNLOAD_MAX_BYTES = 100 * 1024 * 1024 // 100 MB
const ALLOWED_ASSET_HOSTS = new Set([
  'github.com',
  'objects.githubusercontent.com',
  'release-assets.githubusercontent.com',
])
const REPO_SLUG_REGEX = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/

export const ALLOWLIST_DIRS = ['.claude', '.claude-plugin', 'scripts', 'tools']
export const ALLOWLIST_FILES = [
  'README.md',
  'CLAUDE.md',
  'LICENSE',
  'RELEASE.md',
  '.version-bump.json',
  'requirements.txt',
  'SKILL.md',
]

export const PRESERVE_PATHS = [
  '.context',
  '.github/openspec-config.yml',
  'recordings',
  'issue-',
  '.venv',
  'venv',
]

export function validateRepoSlug(repo: string): void {
  if (!REPO_SLUG_REGEX.test(repo)) {
    throw new Error(`Invalid repository slug: ${repo}`)
  }
}

export function getCurrentVersion(root: string): string | undefined {
  const path = join(root, '.version-bump.json')
  if (!existsSync(path)) {
    return undefined
  }
  try {
    const data = JSON.parse(readFileSync(path, 'utf-8'))
    if (typeof data.version === 'string' && data.version) {
      return data.version
    }
  } catch {
    return undefined
  }
  return undefined
}

function parseVersion(version: string): number[] {
  return version.split('.').map((part) => {
    const num = Number(part)
    return Number.isNaN(num) ? 0 : num
  })
}

export function isUpdateNeeded(current: string, latest: string): boolean {
  const currentParts = parseVersion(current)
  const latestParts = parseVersion(latest)
  const maxLength = Math.max(currentParts.length, latestParts.length)
  for (let i = 0; i < maxLength; i++) {
    const currentPart = currentParts[i] ?? 0
    const latestPart = latestParts[i] ?? 0
    if (latestPart > currentPart) {
      return true
    }
    if (latestPart < currentPart) {
      return false
    }
  }
  return false
}

function isSemverTag(tag: string): boolean {
  return /^v?\d+(\.\d+)*$/.test(tag)
}

export async function fetchLatestRelease(repo: string): Promise<ReleaseInfo> {
  validateRepoSlug(repo)
  const url = `${GITHUB_API_BASE}/${repo}/releases/latest`
  const response = await fetch(url, {
    headers: { Accept: 'application/vnd.github+json' },
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
  })
  if (!response.ok) {
    throw new Error(`GitHub API error ${response.status}: ${response.statusText}`)
  }
  const data = (await response.json()) as {
    tag_name: string
    published_at: string
    assets: Array<{ name: string; browser_download_url: string }>
  }
  const version = data.tag_name.replace(/^v/, '')
  if (!isSemverTag(data.tag_name)) {
    throw new Error(`Unexpected release tag: ${data.tag_name}`)
  }
  const asset = data.assets.find((a) => a.name.endsWith('.tar.gz'))
  if (!asset) {
    throw new Error(`No tar.gz asset found for release ${data.tag_name}`)
  }
  const checksumAsset = data.assets.find((a) => a.name === `${asset.name}.sha256`)
  return {
    version,
    assetUrl: asset.browser_download_url,
    publishedAt: data.published_at,
    checksumUrl: checksumAsset?.browser_download_url,
  }
}

function validateAssetUrl(url: string): void {
  const parsed = new URL(url)
  if (parsed.protocol !== 'https:') {
    throw new Error(`Download URL must use HTTPS: ${url}`)
  }
  if (!ALLOWED_ASSET_HOSTS.has(parsed.hostname)) {
    throw new Error(`Unexpected download host: ${parsed.hostname}`)
  }
}

async function fetchAsset(url: string, redirectCount = 0): Promise<Response> {
  if (redirectCount > 5) {
    throw new Error('Too many download redirects')
  }
  validateAssetUrl(url)
  const response = await fetch(url, {
    redirect: 'manual',
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
  })
  if (response.status >= 300 && response.status < 400) {
    const location = response.headers.get('location')
    if (!location) {
      throw new Error(`Redirect without Location header from ${url}`)
    }
    return fetchAsset(new URL(location, url).toString(), redirectCount + 1)
  }
  return response
}

async function writeBodyWithLimit(
  body: ReadableStream<Uint8Array> | null,
  dest: string,
  maxBytes: number
): Promise<void> {
  if (!body) {
    throw new Error('Download response has no body')
  }
  mkdirSync(dirname(dest), { recursive: true })
  const reader = body.getReader()
  const fileStream = createWriteStream(dest)
  let received = 0

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      received += value.byteLength
      if (received > maxBytes) {
        throw new Error(`Download exceeds maximum size of ${maxBytes} bytes`)
      }
      fileStream.write(value)
    }
  } finally {
    fileStream.end()
  }

  await new Promise<void>((resolve, reject) => {
    fileStream.on('finish', resolve)
    fileStream.on('error', reject)
  })
}

export async function downloadAsset(url: string, dest: string): Promise<void> {
  const response = await fetchAsset(url)
  if (!response.ok) {
    throw new Error(`Download failed ${response.status}: ${response.statusText}`)
  }
  await writeBodyWithLimit(response.body, dest, DOWNLOAD_MAX_BYTES)
}

async function verifyChecksum(archivePath: string, checksumUrl: string): Promise<void> {
  const response = await fetchAsset(checksumUrl)
  if (!response.ok) {
    throw new Error(`Checksum download failed ${response.status}: ${response.statusText}`)
  }
  const text = await response.text()
  const expected = text.trim().split(/\s+/)[0]?.toLowerCase()
  if (!expected) {
    throw new Error('Checksum file is empty')
  }
  const actual = await computeSha256(archivePath)
  if (actual !== expected) {
    throw new Error(`Checksum mismatch: expected ${expected}, got ${actual}`)
  }
}

async function computeSha256(filePath: string): Promise<string> {
  const { createHash } = await import('node:crypto')
  const hash = createHash('sha256')
  const { readFile } = await import('node:fs/promises')
  hash.update(await readFile(filePath))
  return hash.digest('hex').toLowerCase()
}

export async function extractArchive(archivePath: string, dest: string): Promise<void> {
  mkdirSync(dest, { recursive: true })
  await extract({
    file: archivePath,
    cwd: dest,
    filter: (_path: string, entry: ReadEntry | import('node:fs').Stats) => {
      const readEntry = entry as ReadEntry
      return readEntry.type === 'File' || readEntry.type === 'Directory'
    },
  })
}

function normalizeRelativePath(relativePath: string): string {
  return relativePath.replace(/\\/g, '/')
}

export function isPreserved(relativePath: string): boolean {
  const posix = normalizeRelativePath(relativePath)
  return PRESERVE_PATHS.some((prefix) => {
    if (posix === prefix) return true
    if (prefix.endsWith('-')) {
      return posix.startsWith(prefix)
    }
    return posix.startsWith(`${prefix}/`)
  })
}

function backupPath(projectRoot: string, relativePath: string): string {
  return resolve(projectRoot, '.context', 'lincoln-update-backup', relativePath)
}

function backupIfExists(projectRoot: string, relativePath: string): void {
  const target = resolve(projectRoot, relativePath)
  if (!existsSync(target)) {
    return
  }
  const backup = backupPath(projectRoot, relativePath)
  mkdirSync(dirname(backup), { recursive: true })
  copyFileSync(target, backup)
}

function restoreBackups(projectRoot: string, relativePaths: string[]): void {
  for (const relativePath of relativePaths) {
    const backup = backupPath(projectRoot, relativePath)
    const target = resolve(projectRoot, relativePath)
    if (existsSync(backup)) {
      mkdirSync(dirname(target), { recursive: true })
      copyFileSync(backup, target)
    }
  }
}

export function resolveStagingRoot(stagingRoot: string): string {
  const entries = readdirSync(stagingRoot, { withFileTypes: true })
  if (entries.length === 1 && entries[0].isDirectory()) {
    return resolve(stagingRoot, entries[0].name)
  }
  return stagingRoot
}

export async function mergeRelease(
  stagingRoot: string,
  projectRoot: string
): Promise<MergeResult> {
  const updated: string[] = []
  const backedUp: string[] = []
  const preservedSet = new Set<string>()
  const resolvedStaging = resolveStagingRoot(stagingRoot)
  const backupDir = resolve(projectRoot, '.context', 'lincoln-update-backup')

  function collectFiles(dir: string): string[] {
    const files: string[] = []
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      if (entry.isSymbolicLink()) {
        continue
      }
      const fullPath = join(dir, entry.name)
      if (entry.isDirectory()) {
        files.push(...collectFiles(fullPath))
      } else if (entry.isFile()) {
        files.push(fullPath)
      }
    }
    return files
  }

  function processSource(sourcePath: string, relativePath: string): void {
    if (isPreserved(relativePath)) {
      const existingTarget = resolve(projectRoot, relativePath)
      if (existsSync(existingTarget)) {
        const topLevel = PRESERVE_PATHS.find((prefix) => {
          const posix = normalizeRelativePath(relativePath)
          if (prefix.endsWith('-')) {
            return posix === prefix || posix.startsWith(prefix)
          }
          return posix === prefix || posix.startsWith(`${prefix}/`)
        })
        if (topLevel) {
          preservedSet.add(topLevel)
        }
      }
      return
    }

    const targetPath = resolve(projectRoot, relativePath)
    backupIfExists(projectRoot, relativePath)
    backedUp.push(relativePath)
    mkdirSync(dirname(targetPath), { recursive: true })
    copyFileSync(sourcePath, targetPath)
    updated.push(relativePath)
  }

  try {
    for (const dirName of ALLOWLIST_DIRS) {
      const sourceDir = join(resolvedStaging, dirName)
      if (!existsSync(sourceDir)) {
        continue
      }
      for (const file of collectFiles(sourceDir)) {
        const rel = relative(sourceDir, file)
        processSource(file, normalizeRelativePath(join(dirName, rel)))
      }
    }

    for (const fileName of ALLOWLIST_FILES) {
      const sourceFile = join(resolvedStaging, fileName)
      if (!existsSync(sourceFile)) {
        continue
      }
      processSource(sourceFile, fileName)
    }

    for (const prefix of PRESERVE_PATHS) {
      if (existsSync(resolve(projectRoot, prefix))) {
        preservedSet.add(prefix)
      }
    }
  } catch (err) {
    restoreBackups(projectRoot, backedUp)
    throw err
  }

  return { updated, preserved: Array.from(preservedSet), backupDir }
}

export async function updateRelease(options: UpdateOptions): Promise<UpdateResult> {
  const { root, repo = DEFAULT_REPO, dryRun = false } = options

  try {
    const currentVersion = getCurrentVersion(root)
    if (!currentVersion) {
      return { success: false, updated: [], preserved: [], error: 'Could not detect current Lincoln version' }
    }

    const latest = await fetchLatestRelease(repo)
    if (!isUpdateNeeded(currentVersion, latest.version)) {
      return {
        success: true,
        fromVersion: currentVersion,
        toVersion: currentVersion,
        updated: [],
        preserved: [],
      }
    }

    if (dryRun) {
      return {
        success: true,
        fromVersion: currentVersion,
        toVersion: latest.version,
        updated: [],
        preserved: [],
      }
    }

    const tempDir = join(root, '.context', 'lincoln-update-staging')
    mkdirSync(tempDir, { recursive: true })

    try {
      const archivePath = join(tempDir, 'lincoln-latest.tar.gz')
      const extractDir = join(tempDir, 'extracted')

      await downloadAsset(latest.assetUrl, archivePath)
      if (latest.checksumUrl) {
        await verifyChecksum(archivePath, latest.checksumUrl)
      }
      await extractArchive(archivePath, extractDir)

      const merge = await mergeRelease(extractDir, root)

      return {
        success: true,
        fromVersion: currentVersion,
        toVersion: latest.version,
        updated: merge.updated,
        preserved: merge.preserved,
        backupDir: merge.backupDir,
      }
    } finally {
      rmSync(tempDir, { recursive: true, force: true })
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return { success: false, updated: [], preserved: [], error: message }
  }
}
