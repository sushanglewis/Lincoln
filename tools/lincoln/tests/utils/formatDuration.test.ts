import { describe, expect, test } from 'vitest'
import { formatDuration } from '../../src/utils/formatDuration'

describe('formatDuration', () => {
  test('formats seconds as mm:ss', () => {
    expect(formatDuration(0)).toBe('00:00')
    expect(formatDuration(5)).toBe('00:05')
    expect(formatDuration(83)).toBe('01:23')
    expect(formatDuration(3661)).toBe('61:01')
  })
})
