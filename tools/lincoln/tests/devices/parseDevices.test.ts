import { describe, expect, test } from 'vitest'
import { parseDevicesOutput } from '../../src/devices/parseDevices'

describe('parseDevicesOutput', () => {
  test('parses default device and device list', () => {
    const output = 'Default input: MacBook Pro Microphone\n  MacBook Pro Microphone\n  External Mic\n'
    const result = parseDevicesOutput(output)
    expect(result.defaultDevice).toBe('MacBook Pro Microphone')
    expect(result.devices).toEqual(['MacBook Pro Microphone', 'External Mic'])
  })

  test('returns null default when the line is missing', () => {
    const result = parseDevicesOutput('  Mic A\n')
    expect(result.defaultDevice).toBeNull()
    expect(result.devices).toEqual(['Mic A'])
  })

  test('returns empty result for empty output', () => {
    expect(parseDevicesOutput('')).toEqual({ defaultDevice: null, devices: [] })
  })
})
