import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, expect, test } from 'vitest'
import { loadConfig, loadConfigOptional } from '../../src/config/loadConfig'

describe('loadConfig', () => {
  test('loads a valid YAML config', () => {
    const dir = mkdtempSync(join(tmpdir(), 'lincoln-config-'))
    const path = join(dir, '.lincolnrc')
    writeFileSync(path, 'default_design_id: checkout-redesign\nshow_audio_meter: true\n', 'utf-8')

    const result = loadConfig(path)

    expect(result.defaultDesignId).toBe('checkout-redesign')
    expect(result.showAudioMeter).toBe(true)
  })

  test('loads a valid JSON config', () => {
    const dir = mkdtempSync(join(tmpdir(), 'lincoln-config-'))
    const path = join(dir, '.lincolnrc.json')
    writeFileSync(path, JSON.stringify({ auto_process: false, audio_meter_style: 'dot' }), 'utf-8')

    const result = loadConfig(path)

    expect(result.autoProcess).toBe(false)
    expect(result.audioMeterStyle).toBe('dot')
  })

  test('throws when config file is missing', () => {
    expect(() => loadConfig('/nonexistent/.lincolnrc')).toThrow('Config file not found')
  })

  test('throws when config file has invalid YAML', () => {
    const dir = mkdtempSync(join(tmpdir(), 'lincoln-config-'))
    const path = join(dir, '.lincolnrc')
    writeFileSync(path, '{ invalid yaml', 'utf-8')

    expect(() => loadConfig(path)).toThrow('Failed to parse config')
  })
})

describe('loadConfigOptional', () => {
  test('returns empty config when file is missing', () => {
    const result = loadConfigOptional('/nonexistent/.lincolnrc')

    expect(result).toEqual({})
  })

  test('returns parsed config when file exists', () => {
    const dir = mkdtempSync(join(tmpdir(), 'lincoln-config-'))
    const path = join(dir, '.lincolnrc')
    writeFileSync(path, 'default_topic: "结算流程 redesign 需求访谈"\n', 'utf-8')

    const result = loadConfigOptional(path)

    expect(result.defaultTopic).toBe('结算流程 redesign 需求访谈')
  })
})
