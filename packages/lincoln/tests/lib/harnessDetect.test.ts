import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { detectGlobalHarnesses } from '../../src/lib/harnessDetect.js'

describe('detectGlobalHarnesses', () => {
  let tmpDir: string

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lincoln-harness-test-'))
  })

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true })
  })

  it('detects claude-code when ~/.claude exists', () => {
    fs.mkdirSync(path.join(tmpDir, '.claude'), { recursive: true })
    const harnesses = detectGlobalHarnesses(tmpDir)
    expect(harnesses.some((h) => h.id === 'claude-code' && h.installed)).toBe(true)
  })

  it('marks claude-code as plugin-managed when plugins/lincoln exists', () => {
    fs.mkdirSync(path.join(tmpDir, '.claude', 'plugins', 'lincoln'), { recursive: true })
    const harnesses = detectGlobalHarnesses(tmpDir)
    const claude = harnesses.find((h) => h.id === 'claude-code')
    expect(claude?.installed).toBe(true)
    expect(claude?.pluginManaged).toBe(true)
  })

  it('reports no installed harnesses in empty home', () => {
    const harnesses = detectGlobalHarnesses(tmpDir)
    expect(harnesses.every((h) => !h.installed)).toBe(true)
  })
})
