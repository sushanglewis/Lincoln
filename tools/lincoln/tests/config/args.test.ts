import { describe, expect, test } from 'vitest'
import { parseArgs } from '../../src/config/args'

describe('parseArgs', () => {
  test('returns defaults when no args are provided', () => {
    const result = parseArgs([])

    expect(result.topic).toBeUndefined()
    expect(result.designId).toBeUndefined()
    expect(result.branch).toBeUndefined()
    expect(result.sessionId).toBeUndefined()
    expect(result.noTui).toBe(false)
    expect(result.help).toBe(false)
  })

  test('parses --topic, --design-id, and --branch', () => {
    const result = parseArgs([
      '--topic',
      '结算流程 redesign 需求访谈',
      '--design-id',
      'checkout-redesign',
      '--branch',
      'pm-workflow-integration-plugin',
    ])

    expect(result.topic).toBe('结算流程 redesign 需求访谈')
    expect(result.designId).toBe('checkout-redesign')
    expect(result.branch).toBe('pm-workflow-integration-plugin')
  })

  test('parses --no-tui', () => {
    const result = parseArgs(['--no-tui'])

    expect(result.noTui).toBe(true)
  })

  test('parses --help', () => {
    const result = parseArgs(['--help'])

    expect(result.help).toBe(true)
  })

  test('ignores unknown options and positional arguments', () => {
    const result = parseArgs(['--unknown', 'value', 'positional'])

    expect(result.topic).toBeUndefined()
    expect(result.noTui).toBe(false)
  })
})
