import { mkdtempSync, mkdirSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, expect, test, afterEach } from 'vitest'
import { detectHarnesses } from '../../src/utils/detectHarness'

describe('detectHarnesses', () => {
  let root: string

  afterEach(() => {
    if (root) rmSync(root, { recursive: true, force: true })
  })

  function setupRoot() {
    root = mkdtempSync(join(tmpdir(), 'lincoln-'))
    return root
  }

  test('detects project-level claude-code harness', () => {
    setupRoot()
    mkdirSync(join(root, '.claude'))
    const harnesses = detectHarnesses(root, root)
    const claude = harnesses.find((h) => h.id === 'claude-code')
    expect(claude?.installed).toBe(true)
  })

  test('detects project-level codex harness', () => {
    setupRoot()
    mkdirSync(join(root, '.codex'))
    const harnesses = detectHarnesses(root, root)
    const codex = harnesses.find((h) => h.id === 'codex')
    expect(codex?.installed).toBe(true)
  })

  test('marks undetected harnesses as not installed', () => {
    setupRoot()
    const harnesses = detectHarnesses(root, root)
    expect(harnesses.every((h) => !h.installed)).toBe(true)
  })
})
