import { createHash } from 'node:crypto'
import { describe, expect, test, vi, afterEach } from 'vitest'
import {
  mkdtempSync,
  mkdirSync,
  writeFileSync,
  rmSync,
  existsSync,
  readFileSync,
} from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { create } from 'tar'
import {
  getCurrentVersion,
  fetchLatestRelease,
  isUpdateNeeded,
  isPreserved,
  downloadAsset,
  extractArchive,
  mergeRelease,
  updateRelease,
  PRESERVE_PATHS,
  type ReleaseInfo,
} from '../../src/utils/updateRelease'

function makeStreamFromBuffer(buffer: Buffer): ReadableStream<Uint8Array> {
  return new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(new Uint8Array(buffer))
      controller.close()
    },
  })
}

function makeTempDir(): string {
  return mkdtempSync(join(tmpdir(), 'lincoln-update-'))
}

function cleanup(dirs: string[]) {
  for (const dir of dirs) {
    rmSync(dir, { recursive: true, force: true })
  }
}

describe('getCurrentVersion', () => {
  const dirs: string[] = []

  afterEach(() => {
    cleanup(dirs)
    dirs.length = 0
  })

  test('reads version from .version-bump.json', () => {
    const root = makeTempDir()
    dirs.push(root)
    writeFileSync(join(root, '.version-bump.json'), JSON.stringify({ version: '1.2.0' }))
    expect(getCurrentVersion(root)).toBe('1.2.0')
  })

  test('returns undefined when .version-bump.json is missing', () => {
    const root = makeTempDir()
    dirs.push(root)
    expect(getCurrentVersion(root)).toBeUndefined()
  })

  test('returns undefined when .version-bump.json lacks version', () => {
    const root = makeTempDir()
    dirs.push(root)
    writeFileSync(join(root, '.version-bump.json'), JSON.stringify({ manifests: [] }))
    expect(getCurrentVersion(root)).toBeUndefined()
  })
})

describe('isUpdateNeeded', () => {
  test('returns true when latest is greater', () => {
    expect(isUpdateNeeded('1.2.0', '1.3.0')).toBe(true)
    expect(isUpdateNeeded('1.2.0', '2.0.0')).toBe(true)
  })

  test('returns false when versions are equal', () => {
    expect(isUpdateNeeded('1.3.0', '1.3.0')).toBe(false)
  })

  test('returns false when current is newer', () => {
    expect(isUpdateNeeded('1.3.0', '1.2.0')).toBe(false)
  })
})

describe('fetchLatestRelease', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  test('returns asset URL for tar.gz asset', async () => {
    const release = {
      tag_name: 'v1.3.0',
      published_at: '2026-07-27T00:00:00Z',
      assets: [
        { name: 'lincoln-1.3.0.tar.gz', browser_download_url: 'https://example.com/lincoln-1.3.0.tar.gz' },
        { name: 'lincoln-1.3.0.zip', browser_download_url: 'https://example.com/lincoln-1.3.0.zip' },
      ],
    }
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => release,
    } as Response)

    const result = await fetchLatestRelease('sushanglewis/Lincoln')
    expect(result.version).toBe('1.3.0')
    expect(result.assetUrl).toBe('https://example.com/lincoln-1.3.0.tar.gz')
    expect(result.publishedAt).toBe('2026-07-27T00:00:00Z')
  })

  test('throws when GitHub API fails', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      statusText: 'Forbidden',
    } as Response)

    await expect(fetchLatestRelease('sushanglewis/Lincoln')).rejects.toThrow('GitHub API error')
  })

  test('throws when no tar.gz asset exists', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        tag_name: 'v1.3.0',
        published_at: '2026-07-27T00:00:00Z',
        assets: [{ name: 'lincoln-1.3.0.zip', browser_download_url: 'https://example.com/lincoln-1.3.0.zip' }],
      }),
    } as Response)

    await expect(fetchLatestRelease('sushanglewis/Lincoln')).rejects.toThrow('No tar.gz asset')
  })
})

describe('downloadAsset', () => {
  const dirs: string[] = []

  afterEach(() => {
    vi.restoreAllMocks()
    cleanup(dirs)
    dirs.length = 0
  })

  test('writes downloaded stream to destination', async () => {
    const destDir = makeTempDir()
    dirs.push(destDir)
    const destPath = join(destDir, 'lincoln.tgz')

    const content = Buffer.from('fake archive bytes')
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: makeStreamFromBuffer(content),
    } as Response)

    await downloadAsset('https://github.com/lincoln.tgz', destPath)

    expect(existsSync(destPath)).toBe(true)
    expect(readFileSync(destPath)).toEqual(content)
  })

  test('throws when download fails', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    } as Response)

    const destDir = makeTempDir()
    dirs.push(destDir)
    await expect(downloadAsset('https://github.com/lincoln.tgz', join(destDir, 'lincoln.tgz'))).rejects.toThrow(
      'Download failed'
    )
  })

  test('rejects unexpected download host', async () => {
    const destDir = makeTempDir()
    dirs.push(destDir)
    await expect(downloadAsset('https://example.com/lincoln.tgz', join(destDir, 'lincoln.tgz'))).rejects.toThrow(
      'Unexpected download host'
    )
  })
})

describe('extractArchive', () => {
  const dirs: string[] = []

  afterEach(() => {
    cleanup(dirs)
    dirs.length = 0
  })

  test('extracts tar.gz archive', async () => {
    const sourceDir = makeTempDir()
    const archiveDir = makeTempDir()
    const extractDir = makeTempDir()
    dirs.push(sourceDir, archiveDir, extractDir)

    mkdirSync(join(sourceDir, 'scripts'))
    writeFileSync(join(sourceDir, 'scripts', 'lincoln-setup.py'), 'setup')
    writeFileSync(join(sourceDir, 'README.md'), 'hello')

    const archivePath = join(archiveDir, 'lincoln.tgz')
    await create(
      {
        gzip: true,
        file: archivePath,
        cwd: sourceDir,
      },
      ['.']
    )

    await extractArchive(archivePath, extractDir)

    expect(existsSync(join(extractDir, 'scripts', 'lincoln-setup.py'))).toBe(true)
    expect(readFileSync(join(extractDir, 'README.md'), 'utf-8')).toBe('hello')
  })
})

describe('mergeRelease', () => {
  const dirs: string[] = []

  afterEach(() => {
    cleanup(dirs)
    dirs.length = 0
  })

  test('copies allowlisted files and preserves user data', async () => {
    const staging = makeTempDir()
    const project = makeTempDir()
    dirs.push(staging, project)

    mkdirSync(join(staging, '.claude'))
    writeFileSync(join(staging, '.claude', 'skills.yaml'), 'new skills')
    writeFileSync(join(staging, 'README.md'), 'new readme')

    mkdirSync(join(project, '.claude'))
    writeFileSync(join(project, '.claude', 'skills.yaml'), 'old skills')
    mkdirSync(join(project, '.context'))
    writeFileSync(join(project, '.context', 'lc-setup-state.yaml'), 'user state')
    writeFileSync(join(project, 'README.md'), 'old readme')

    const result = await mergeRelease(staging, project)

    expect(readFileSync(join(project, '.claude', 'skills.yaml'), 'utf-8')).toBe('new skills')
    expect(readFileSync(join(project, 'README.md'), 'utf-8')).toBe('new readme')
    expect(readFileSync(join(project, '.context', 'lc-setup-state.yaml'), 'utf-8')).toBe('user state')
    expect(result.updated).toContain('README.md')
    expect(result.updated).toContain('.claude/skills.yaml')
    expect(result.preserved).toContain('.context')
  })

  test('creates backup before overwriting', async () => {
    const staging = makeTempDir()
    const project = makeTempDir()
    dirs.push(staging, project)

    writeFileSync(join(staging, 'README.md'), 'new')
    writeFileSync(join(project, 'README.md'), 'old')

    await mergeRelease(staging, project)

    const backupDir = resolve(project, '.context', 'lincoln-update-backup')
    expect(existsSync(backupDir)).toBe(true)
    expect(existsSync(join(backupDir, 'README.md'))).toBe(true)
    expect(readFileSync(join(backupDir, 'README.md'), 'utf-8')).toBe('old')
  })

  test('restores backups when merge fails', async () => {
    const staging = makeTempDir()
    const project = makeTempDir()
    dirs.push(staging, project)

    writeFileSync(join(staging, 'README.md'), 'new')
    mkdirSync(join(project, 'README.md'))
    writeFileSync(join(project, 'README.md', 'nested'), 'existing')

    await expect(mergeRelease(staging, project)).rejects.toThrow()
    expect(readFileSync(join(project, 'README.md', 'nested'), 'utf-8')).toBe('existing')
  })
})

describe('PRESERVE_PATHS', () => {
  test('includes user data directories and config files', () => {
    expect(PRESERVE_PATHS).toContain('.context')
    expect(PRESERVE_PATHS).toContain('.github/openspec-config.yml')
    expect(PRESERVE_PATHS).toContain('recordings')
    expect(PRESERVE_PATHS).toContain('issue-')
  })
})

describe('getCurrentVersion edge cases', () => {
  const dirs: string[] = []

  afterEach(() => {
    cleanup(dirs)
    dirs.length = 0
  })

  test('returns undefined when .version-bump.json is malformed', () => {
    const root = makeTempDir()
    dirs.push(root)
    writeFileSync(join(root, '.version-bump.json'), 'not json')
    expect(getCurrentVersion(root)).toBeUndefined()
  })
})

describe('isUpdateNeeded edge cases', () => {
  test('handles versions with different lengths', () => {
    expect(isUpdateNeeded('1.2', '1.2.0')).toBe(false)
    expect(isUpdateNeeded('1.2', '1.3.0')).toBe(true)
    expect(isUpdateNeeded('1.2.0', '1.2')).toBe(false)
  })

  test('treats non-numeric parts as zero', () => {
    expect(isUpdateNeeded('1.x.0', '1.0.0')).toBe(false)
    expect(isUpdateNeeded('1.0.0', '1.x.0')).toBe(false)
  })
})

describe('mergeRelease edge cases', () => {
  const dirs: string[] = []

  afterEach(() => {
    cleanup(dirs)
    dirs.length = 0
  })

  test('resolves single top-level directory in staging', async () => {
    const staging = makeTempDir()
    const project = makeTempDir()
    dirs.push(staging, project)

    const inner = join(staging, 'lincoln-1.3.0')
    mkdirSync(inner)
    mkdirSync(join(inner, '.claude'))
    writeFileSync(join(inner, '.claude', 'skills.yaml'), 'new skills')

    const result = await mergeRelease(staging, project)

    expect(result.updated).toContain('.claude/skills.yaml')
    expect(readFileSync(join(project, '.claude', 'skills.yaml'), 'utf-8')).toBe('new skills')
  })

  test('skips missing allowlist directories and files', async () => {
    const staging = makeTempDir()
    const project = makeTempDir()
    dirs.push(staging, project)

    writeFileSync(join(staging, 'README.md'), 'new readme')

    const result = await mergeRelease(staging, project)

    expect(result.updated).toContain('README.md')
    expect(result.updated).not.toContain('.version-bump.json')
  })

  test('does not list preserved paths that do not exist in project', async () => {
    const staging = makeTempDir()
    const project = makeTempDir()
    dirs.push(staging, project)

    mkdirSync(join(staging, '.context'))
    writeFileSync(join(staging, '.context', 'lc-setup-state.yaml'), 'new state')

    const result = await mergeRelease(staging, project)

    expect(result.preserved).not.toContain('.context')
    expect(existsSync(join(project, '.context', 'lc-setup-state.yaml'))).toBe(false)
  })

  test('detects issue- prefixed preserved paths', () => {
    expect(isPreserved('issue-123/notes.md')).toBe(true)
    expect(isPreserved('issue-123')).toBe(true)
  })

  test('detects exact preserved paths', () => {
    expect(isPreserved('.context/lc-setup-state.yaml')).toBe(true)
    expect(isPreserved('.context')).toBe(true)
  })

  test('returns false for non-preserved paths', () => {
    expect(isPreserved('README.md')).toBe(false)
    expect(isPreserved('.claude/skills.yaml')).toBe(false)
  })
})

describe('updateRelease orchestrator', () => {
  const dirs: string[] = []

  afterEach(() => {
    vi.restoreAllMocks()
    cleanup(dirs)
    dirs.length = 0
  })

  test('returns error when current version cannot be detected', async () => {
    const root = makeTempDir()
    dirs.push(root)

    const result = await updateRelease({ root })

    expect(result.success).toBe(false)
    expect(result.error).toContain('Could not detect current Lincoln version')
  })

  test('returns up-to-date result when latest is not newer', async () => {
    const root = makeTempDir()
    dirs.push(root)
    writeFileSync(join(root, '.version-bump.json'), JSON.stringify({ version: '1.3.0' }))

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        tag_name: 'v1.3.0',
        published_at: '2026-07-27T00:00:00Z',
        assets: [{ name: 'lincoln-1.3.0.tar.gz', browser_download_url: 'https://example.com/lincoln-1.3.0.tar.gz' }],
      }),
    } as Response)

    const result = await updateRelease({ root })

    expect(result.success).toBe(true)
    expect(result.fromVersion).toBe('1.3.0')
    expect(result.toVersion).toBe('1.3.0')
    expect(result.updated).toEqual([])
    expect(result.preserved).toEqual([])
  })

  test('returns dry-run result without downloading', async () => {
    const root = makeTempDir()
    dirs.push(root)
    writeFileSync(join(root, '.version-bump.json'), JSON.stringify({ version: '1.2.0' }))

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        tag_name: 'v1.3.0',
        published_at: '2026-07-27T00:00:00Z',
        assets: [{ name: 'lincoln-1.3.0.tar.gz', browser_download_url: 'https://example.com/lincoln-1.3.0.tar.gz' }],
      }),
    } as Response)

    const result = await updateRelease({ root, dryRun: true })

    expect(result.success).toBe(true)
    expect(result.fromVersion).toBe('1.2.0')
    expect(result.toVersion).toBe('1.3.0')
    expect(global.fetch).toHaveBeenCalledTimes(1)
  })

  test('downloads and merges release when update is available', async () => {
    const root = makeTempDir()
    const archiveDir = makeTempDir()
    dirs.push(root, archiveDir)

    writeFileSync(join(root, '.version-bump.json'), JSON.stringify({ version: '1.2.0' }))

    mkdirSync(join(archiveDir, 'source', '.claude'), { recursive: true })
    writeFileSync(join(archiveDir, 'source', '.claude', 'skills.yaml'), 'new skills')
    writeFileSync(join(archiveDir, 'source', 'README.md'), 'new readme')

    const archivePath = join(archiveDir, 'lincoln-1.3.0.tar.gz')
    await create({ gzip: true, file: archivePath, cwd: join(archiveDir, 'source') }, ['.'])
    const archiveBuffer = Buffer.from(readFileSync(archivePath))

    global.fetch = vi.fn().mockImplementation(async (url: string | URL | Request) => {
      const urlString = String(url)
      if (urlString.includes('api.github.com')) {
        return {
          ok: true,
          json: async () => ({
            tag_name: 'v1.3.0',
            published_at: '2026-07-27T00:00:00Z',
            assets: [{ name: 'lincoln-1.3.0.tar.gz', browser_download_url: 'https://github.com/lincoln-1.3.0.tar.gz' }],
          }),
        } as Response
      }
      return {
        ok: true,
        body: makeStreamFromBuffer(archiveBuffer),
      } as Response
    })

    const result = await updateRelease({ root })

    expect(result.success).toBe(true)
    expect(result.fromVersion).toBe('1.2.0')
    expect(result.toVersion).toBe('1.3.0')
    expect(result.updated).toContain('README.md')
    expect(result.updated).toContain('.claude/skills.yaml')
  })

  test('verifies checksum when sha256 asset is present', async () => {
    const root = makeTempDir()
    const archiveDir = makeTempDir()
    dirs.push(root, archiveDir)

    writeFileSync(join(root, '.version-bump.json'), JSON.stringify({ version: '1.2.0' }))

    mkdirSync(join(archiveDir, 'source', '.claude'), { recursive: true })
    writeFileSync(join(archiveDir, 'source', '.claude', 'skills.yaml'), 'new skills')
    writeFileSync(join(archiveDir, 'source', 'README.md'), 'new readme')

    const archivePath = join(archiveDir, 'lincoln-1.3.0.tar.gz')
    await create({ gzip: true, file: archivePath, cwd: join(archiveDir, 'source') }, ['.'])
    const archiveBuffer = Buffer.from(readFileSync(archivePath))
    const checksum = createHash('sha256').update(archiveBuffer).digest('hex')

    global.fetch = vi.fn().mockImplementation(async (url: string | URL | Request) => {
      const urlString = String(url)
      if (urlString.includes('api.github.com')) {
        return {
          ok: true,
          json: async () => ({
            tag_name: 'v1.3.0',
            published_at: '2026-07-27T00:00:00Z',
            assets: [
              { name: 'lincoln-1.3.0.tar.gz', browser_download_url: 'https://github.com/lincoln-1.3.0.tar.gz' },
              { name: 'lincoln-1.3.0.tar.gz.sha256', browser_download_url: 'https://github.com/lincoln-1.3.0.tar.gz.sha256' },
            ],
          }),
        } as Response
      }
      if (urlString.endsWith('.sha256')) {
        return {
          ok: true,
          text: async () => `${checksum}  lincoln-1.3.0.tar.gz`,
        } as Response
      }
      return {
        ok: true,
        body: makeStreamFromBuffer(archiveBuffer),
      } as Response
    })

    const result = await updateRelease({ root })

    expect(result.success).toBe(true)
    expect(result.toVersion).toBe('1.3.0')
    expect(result.updated).toContain('.claude/skills.yaml')
  })

  test('returns error when fetchLatestRelease fails', async () => {
    const root = makeTempDir()
    dirs.push(root)
    writeFileSync(join(root, '.version-bump.json'), JSON.stringify({ version: '1.2.0' }))

    global.fetch = vi.fn().mockRejectedValue(new Error('network error'))

    const result = await updateRelease({ root })

    expect(result.success).toBe(false)
    expect(result.error).toContain('network error')
  })
})
