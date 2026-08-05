import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { resolveLincolnPaths } from '../../src/lib/paths.js'
import {
  readVersionMarker,
  writeVersionMarker,
  isUpToDate
} from '../../src/lib/versionMarker.js'

describe('versionMarker', () => {
  let tmpDir: string

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lincoln-test-'))
  })

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true })
  })

  it('returns undefined when marker is missing', () => {
    const paths = resolveLincolnPaths(tmpDir)
    expect(readVersionMarker(paths)).toBeUndefined()
  })

  it('writes and reads marker', () => {
    const paths = resolveLincolnPaths(tmpDir)
    const marker = {
      version: '1.6.0',
      installedAt: new Date().toISOString(),
      harnesses: ['claude-code'],
      managedFiles: ['.claude/agents/default.md']
    }
    writeVersionMarker(paths, marker)
    expect(readVersionMarker(paths)).toEqual(marker)
  })

  it('detects up-to-date version', () => {
    const paths = resolveLincolnPaths(tmpDir)
    writeVersionMarker(paths, {
      version: '1.6.0',
      installedAt: new Date().toISOString(),
      harnesses: [],
      managedFiles: []
    })
    expect(isUpToDate(paths, '1.6.0')).toBe(true)
    expect(isUpToDate(paths, '1.7.0')).toBe(false)
  })
})
