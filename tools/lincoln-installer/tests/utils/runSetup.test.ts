import { describe, expect, test } from 'vitest'
import { runSetup, parseJsonOutput } from '../../src/utils/runSetup'

describe('runSetup', () => {
  test('runs a successful command and captures stdout', async () => {
    const result = await runSetup({ root: process.cwd(), command: 'node', args: ['-e', 'console.log("ok")'] })
    expect(result.success).toBe(true)
    expect(result.code).toBe(0)
    expect(result.stdout.trim()).toBe('ok')
  })

  test('returns failure for non-zero exit', async () => {
    const result = await runSetup({ root: process.cwd(), command: 'node', args: ['-e', 'process.exit(1)'] })
    expect(result.success).toBe(false)
    expect(result.code).toBe(1)
  })

  test('returns error when command is missing', async () => {
    const result = await runSetup({ root: process.cwd(), command: 'this-command-does-not-exist-12345', args: [] })
    expect(result.success).toBe(false)
    expect(result.error).toBeTruthy()
  })
})

describe('parseJsonOutput', () => {
  test('parses single JSON line', () => {
    expect(parseJsonOutput('{"ok":true}')).toEqual({ ok: true })
  })

  test('parses last JSON line from mixed output', () => {
    expect(parseJsonOutput('log line\n{"ok":true}')).toEqual({ ok: true })
  })

  test('returns undefined for empty output', () => {
    expect(parseJsonOutput('')).toBeUndefined()
  })

  test('returns undefined for invalid JSON', () => {
    expect(parseJsonOutput('not json')).toBeUndefined()
  })

  test('returns undefined for whitespace-only output', () => {
    expect(parseJsonOutput('   ')).toBeUndefined()
  })
})
