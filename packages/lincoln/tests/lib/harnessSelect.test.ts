import { describe, it, expect } from 'vitest'
import {
  buildHarnessOptions,
  resolveHarnessSelection,
  HARNESS_LABELS
} from '../../src/lib/harnessSelect.js'
import type { GlobalHarnessInfo } from '../../src/lib/harnessDetect.js'

describe('buildHarnessOptions', () => {
  it('pre-checks installed harnesses', () => {
    const detected: GlobalHarnessInfo[] = [
      { id: 'claude-code', installed: true, configDir: '/home/.claude', pluginManaged: false },
      { id: 'codex', installed: false, configDir: '/home/.codex', pluginManaged: false },
      { id: 'opencode', installed: true, configDir: '/home/.opencode', pluginManaged: false }
    ]
    const options = buildHarnessOptions(detected)
    expect(options).toEqual([
      { id: 'claude-code', label: HARNESS_LABELS['claude-code'], checked: true },
      { id: 'codex', label: HARNESS_LABELS['codex'], checked: false },
      { id: 'opencode', label: HARNESS_LABELS['opencode'], checked: true }
    ])
  })
})

describe('resolveHarnessSelection', () => {
  const detected: GlobalHarnessInfo[] = [
    { id: 'claude-code', installed: true, configDir: '/home/.claude', pluginManaged: false },
    { id: 'codex', installed: false, configDir: '/home/.codex', pluginManaged: false },
    { id: 'opencode', installed: true, configDir: '/home/.opencode', pluginManaged: false }
  ]

  it('returns detected harnesses when selection is undefined', () => {
    expect(resolveHarnessSelection(detected, undefined)).toEqual(['claude-code', 'opencode'])
  })

  it('filters selection to valid harness ids', () => {
    expect(resolveHarnessSelection(detected, ['claude-code', 'codex'])).toEqual([
      'claude-code',
      'codex'
    ])
  })

  it('deduplicates selected ids', () => {
    expect(resolveHarnessSelection(detected, ['claude-code', 'claude-code'])).toEqual([
      'claude-code'
    ])
  })

  it('ignores invalid ids', () => {
    expect(resolveHarnessSelection(detected, ['claude-code', 'cursor'])).toEqual(['claude-code'])
  })

  it('returns empty array when selection is empty', () => {
    expect(resolveHarnessSelection(detected, [])).toEqual([])
  })
})
