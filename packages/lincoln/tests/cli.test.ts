import { describe, it, expect } from 'vitest'
import { parseArgs } from '../src/cli.js'

describe('parseArgs', () => {
  it('returns help for empty argv', () => {
    const result = parseArgs(['node', 'lincoln'])
    expect(result.command).toBe('help')
  })

  it('returns help for --help', () => {
    const result = parseArgs(['node', 'lincoln', '--help'])
    expect(result.command).toBe('help')
  })

  it('returns help for unknown command', () => {
    const result = parseArgs(['node', 'lincoln', 'unknown'])
    expect(result.command).toBe('help')
  })

  it('parses install command', () => {
    const result = parseArgs(['node', 'lincoln', 'install', '--yes'])
    expect(result.command).toBe('install')
    expect(result.flags).toEqual({ yes: true })
  })

  it('parses use command with version argument', () => {
    const result = parseArgs(['node', 'lincoln', 'use', '1.6.0'])
    expect(result.command).toBe('use')
    expect(result.args).toEqual(['1.6.0'])
  })
})
