import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { detectGlobalHarnesses, installedHarnessIds, isValidHarnessId } from '../../src/lib/harnessDetect.js'

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

  it('detects codex and opencode when their config dirs exist', () => {
    fs.mkdirSync(path.join(tmpDir, '.codex'), { recursive: true })
    fs.mkdirSync(path.join(tmpDir, '.opencode'), { recursive: true })
    const harnesses = detectGlobalHarnesses(tmpDir)
    expect(harnesses.some((h) => h.id === 'codex' && h.installed)).toBe(true)
    expect(harnesses.some((h) => h.id === 'opencode' && h.installed)).toBe(true)
  })

  it('reports no installed harnesses in empty home', () => {
    const harnesses = detectGlobalHarnesses(tmpDir)
    expect(harnesses.every((h) => !h.installed)).toBe(true)
  })
})

describe('installedHarnessIds', () => {
  let tmpDir: string

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lincoln-harness-ids-test-'))
  })

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true })
  })

  it('returns ids of installed harnesses only', () => {
    fs.mkdirSync(path.join(tmpDir, '.claude'), { recursive: true })
    fs.mkdirSync(path.join(tmpDir, '.opencode'), { recursive: true })
    expect(installedHarnessIds(tmpDir)).toEqual(['claude-code', 'opencode'])
  })
})

describe('isValidHarnessId', () => {
  it('returns true for supported harness ids', () => {
    expect(isValidHarnessId('claude-code')).toBe(true)
    expect(isValidHarnessId('codex')).toBe(true)
    expect(isValidHarnessId('opencode')).toBe(true)
  })

  it('returns false for unsupported values', () => {
    expect(isValidHarnessId('cursor')).toBe(false)
    expect(isValidHarnessId('unknown')).toBe(false)
    expect(isValidHarnessId('')).toBe(false)
  })
})
