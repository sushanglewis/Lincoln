import { describe, expect, test } from 'vitest'
import { amplitudeToMeter } from '../../src/utils/amplitudeToMeter'

describe('amplitudeToMeter', () => {
  test('returns 0 bars for zero amplitude', () => {
    expect(amplitudeToMeter(0, 10)).toBe(0)
  })

  test('returns max bars for full amplitude', () => {
    expect(amplitudeToMeter(1, 10)).toBe(10)
  })

  test('scales linearly between 0 and max', () => {
    expect(amplitudeToMeter(0.5, 10)).toBe(5)
    expect(amplitudeToMeter(0.23, 10)).toBe(2)
  })

  test('clamps out-of-range values', () => {
    expect(amplitudeToMeter(-0.5, 10)).toBe(0)
    expect(amplitudeToMeter(1.5, 10)).toBe(10)
  })
})
