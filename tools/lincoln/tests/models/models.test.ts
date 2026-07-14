import { mkdtempSync, mkdirSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, expect, test } from 'vitest'
import { KNOWN_MODELS, listModelStatuses, modelCachePath } from '../../src/models/models'

describe('models', () => {
  test('KNOWN_MODELS includes common whisper models', () => {
    expect(KNOWN_MODELS).toContain('tiny')
    expect(KNOWN_MODELS).toContain('base')
    expect(KNOWN_MODELS).toContain('large-v3')
  })

  test('modelCachePath returns the ggml path under the engine dir', () => {
    expect(modelCachePath('base', '/cache')).toBe('/cache/whisper/ggml-base.bin')
  })

  test('listModelStatuses marks cached and missing models', () => {
    const dir = mkdtempSync(join(tmpdir(), 'lincoln-models-'))
    mkdirSync(join(dir, 'whisper'), { recursive: true })
    writeFileSync(join(dir, 'whisper', 'ggml-base.bin'), 'fake')

    const statuses = listModelStatuses(dir)
    expect(statuses.find(s => s.name === 'base')?.cached).toBe(true)
    expect(statuses.find(s => s.name === 'small')?.cached).toBe(false)
  })
})
