import { describe, expect, test } from 'vitest'
import { parseWarmupProgress } from '../../src/models/warmupProgress'

describe('parseWarmupProgress', () => {
  test('parses progress with a total', () => {
    expect(parseWarmupProgress('\r  downloaded 512 / 1024 bytes (50.0%)')).toEqual({
      downloaded: 512,
      total: 1024,
      percent: 50,
    })
  })

  test('parses progress without a total', () => {
    expect(parseWarmupProgress('\r  downloaded 512 bytes')).toEqual({
      downloaded: 512,
      total: null,
      percent: null,
    })
  })

  test('returns null for unrelated lines', () => {
    expect(parseWarmupProgress("Warming up whisper model 'base'")).toBeNull()
    expect(parseWarmupProgress('Model ready at /tmp/x')).toBeNull()
  })
})
