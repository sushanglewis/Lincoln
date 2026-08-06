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

  it('parses --harnesses as a value flag', () => {
    const result = parseArgs(['node', 'lincoln', 'install', '--harnesses', 'claude-code,codex'])
    expect(result.command).toBe('install')
    expect(result.flags.harnesses).toBe('claude-code,codex')
  })

  it('parses --no-interactive as a boolean flag', () => {
    const result = parseArgs(['node', 'lincoln', 'install', '--no-interactive'])
    expect(result.command).toBe('install')
    expect(result.flags['no-interactive']).toBe(true)
  })

  it('parses use command with version argument', () => {
    const result = parseArgs(['node', 'lincoln', 'use', '1.6.0'])
    expect(result.command).toBe('use')
    expect(result.args).toEqual(['1.6.0'])
  })

  it('does not consume the version positional after a boolean --yes flag', () => {
    const result = parseArgs(['node', 'lincoln', 'use', '--yes', '1.6.0'])
    expect(result.command).toBe('use')
    expect(result.args).toEqual(['1.6.0'])
    expect(result.flags.yes).toBe(true)
  })

  it('does not consume the version positional after a boolean -y flag', () => {
    const result = parseArgs(['node', 'lincoln', 'use', '-y', '1.6.0'])
    expect(result.command).toBe('use')
    expect(result.args).toEqual(['1.6.0'])
    expect(result.flags.y).toBe(true)
  })

  it('keeps boolean flags boolean when followed by another flag', () => {
    const result = parseArgs(['node', 'lincoln', 'update', '--check', '--dry-run'])
    expect(result.command).toBe('update')
    expect(result.flags).toEqual({ check: true, 'dry-run': true })
  })

  it('still captures values for flags not in the boolean allowlist', () => {
    const result = parseArgs(['node', 'lincoln', 'install', '--config', 'lincoln.yaml'])
    expect(result.command).toBe('install')
    expect(result.flags.config).toBe('lincoln.yaml')
  })

  it('parses --version as a boolean flag', () => {
    const result = parseArgs(['node', 'lincoln', '--version'])
    expect(result.flags.version).toBe(true)
  })

  it('parses -v as a boolean flag', () => {
    const result = parseArgs(['node', 'lincoln', '-v'])
    expect(result.flags.v).toBe(true)
  })
})
