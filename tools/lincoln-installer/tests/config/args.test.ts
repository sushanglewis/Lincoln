import { describe, expect, test } from 'vitest'
import { parseArgs } from '../../src/config/args'

describe('parseArgs', () => {
  test('returns defaults for empty argv', () => {
    const args = parseArgs([])
    expect(args.root).toBe('.')
    expect(args.harness).toEqual([])
    expect(args.yes).toBe(false)
    expect(args.dryRun).toBe(false)
    expect(args.noTui).toBe(false)
    expect(args.format).toBe('human')
    expect(args.help).toBe(false)
  })

  test('parses --root', () => {
    const args = parseArgs(['--root', '/tmp/proj'])
    expect(args.root).toBe('/tmp/proj')
  })

  test('throws when --root is missing value', () => {
    expect(() => parseArgs(['--root'])).toThrow('Missing value for --root')
  })

  test('throws when --root value is another flag', () => {
    expect(() => parseArgs(['--root', '--yes'])).toThrow('Missing value for --root')
  })

  test('collects multiple --harness values', () => {
    const args = parseArgs(['--harness', 'claude-code', '--harness', 'codex'])
    expect(args.harness).toEqual(['claude-code', 'codex'])
  })

  test('throws when --harness is missing value', () => {
    expect(() => parseArgs(['--harness'])).toThrow('Missing value for --harness')
  })

  test('parses boolean flags', () => {
    const args = parseArgs(['--yes', '--dry-run', '--no-tui'])
    expect(args.yes).toBe(true)
    expect(args.dryRun).toBe(true)
    expect(args.noTui).toBe(true)
  })

  test('parses --format json', () => {
    const args = parseArgs(['--format', 'json'])
    expect(args.format).toBe('json')
  })

  test('throws on invalid format', () => {
    expect(() => parseArgs(['--format', 'xml'])).toThrow("Invalid value for --format: xml")
  })

  test('throws when --format is missing value', () => {
    expect(() => parseArgs(['--format'])).toThrow('Missing value for --format')
  })

  test('sets help for --help and -h', () => {
    expect(parseArgs(['--help']).help).toBe(true)
    expect(parseArgs(['-h']).help).toBe(true)
  })

  test('throws on unknown argument', () => {
    expect(() => parseArgs(['--unknown'])).toThrow('Unknown argument: --unknown')
  })
})
