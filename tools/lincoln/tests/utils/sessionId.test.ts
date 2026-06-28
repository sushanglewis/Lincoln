import { describe, expect, test } from 'vitest'
import { generateSessionId } from '../../src/utils/sessionId'

describe('generateSessionId', () => {
  test('uses date and descriptor', () => {
    const result = generateSessionId({
      now: new Date('2026-06-28T10:00:00Z'),
      descriptor: 'stakeholder-checkout',
    })

    expect(result).toBe('2026-06-28-stakeholder-checkout')
  })

  test('falls back to recording when no descriptor', () => {
    const result = generateSessionId({ now: new Date('2026-06-28T10:00:00Z') })

    expect(result).toBe('2026-06-28-recording')
  })

  test('slugifies descriptors with spaces and special characters', () => {
    const result = generateSessionId({
      now: new Date('2026-06-28T10:00:00Z'),
      descriptor: '结算流程 redesign 需求访谈!',
    })

    expect(result).toMatch(/^2026-06-28-/)
    expect(result).not.toContain(' ')
    expect(result).not.toContain('!')
  })
})
