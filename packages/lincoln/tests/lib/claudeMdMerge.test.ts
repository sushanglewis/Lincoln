import { describe, it, expect } from 'vitest'
import { mergeManagedBlock, extractManagedBlock } from '../../src/lib/claudeMdMerge.js'

describe('mergeManagedBlock', () => {
  it('inserts managed block when absent', () => {
    const result = mergeManagedBlock('', '# Lincoln\n')
    expect(result).toContain('<!-- lincoln:begin -->')
    expect(result).toContain('<!-- lincoln:end -->')
    expect(result).toContain('# Lincoln')
  })

  it('replaces existing managed block', () => {
    const existing = '# User\n\n<!-- lincoln:begin -->\nOld\n<!-- lincoln:end -->\n'
    const result = mergeManagedBlock(existing, '# New')
    expect(result).toContain('# New')
    expect(result).not.toContain('Old')
    expect(result).toContain('# User')
  })

  it('preserves content outside managed block', () => {
    const existing = 'Before\n\n<!-- lincoln:begin -->\nManaged\n<!-- lincoln:end -->\n\nAfter'
    const result = mergeManagedBlock(existing, 'Updated')
    expect(result).toContain('Before')
    expect(result).toContain('After')
    expect(result).toContain('Updated')
    expect(result).not.toContain('Managed')
  })
})

describe('extractManagedBlock', () => {
  it('extracts managed block content', () => {
    const existing = '<!-- lincoln:begin -->\nHello\n<!-- lincoln:end -->'
    expect(extractManagedBlock(existing)).toBe('Hello')
  })

  it('returns undefined when no block', () => {
    expect(extractManagedBlock('no block')).toBeUndefined()
  })
})
