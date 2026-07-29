import { describe, expect, test } from 'vitest'
import { parseUpdateArgs } from '../../src/config/updateArgs'

describe('parseUpdateArgs', () => {
  test('returns defaults for empty argv', () => {
    const args = parseUpdateArgs([])
    expect(args.root).toBe('.')
    expect(args.repo).toBe('sushanglewis/Lincoln')
    expect(args.dryRun).toBe(false)
    expect(args.noTui).toBe(false)
    expect(args.format).toBe('human')
    expect(args.help).toBe(false)
  })

  test('parses --root', () => {
    const args = parseUpdateArgs(['--root', '/tmp/proj'])
    expect(args.root).toBe('/tmp/proj')
  })

  test('throws when --root value is missing', () => {
    expect(() => parseUpdateArgs(['--root'])).toThrow('Missing value for --root')
  })

  test('parses --repo', () => {
    const args = parseUpdateArgs(['--repo', 'owner/repo'])
    expect(args.repo).toBe('owner/repo')
  })

  test('parses --dry-run and --no-tui', () => {
    const args = parseUpdateArgs(['--dry-run', '--no-tui'])
    expect(args.dryRun).toBe(true)
    expect(args.noTui).toBe(true)
  })

  test('parses --format json', () => {
    const args = parseUpdateArgs(['--format', 'json'])
    expect(args.format).toBe('json')
  })

  test('throws on invalid --format', () => {
    expect(() => parseUpdateArgs(['--format', 'xml'])).toThrow('Invalid value for --format: xml')
  })

  test('sets help for --help and -h', () => {
    expect(parseUpdateArgs(['--help']).help).toBe(true)
    expect(parseUpdateArgs(['-h']).help).toBe(true)
  })

  test('throws on invalid repository slug', () => {
    expect(() => parseUpdateArgs(['--repo', 'invalid'])).toThrow('Invalid repository slug')
  })
})
