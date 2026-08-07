import { describe, it, expect } from 'vitest'
import { PassThrough } from 'node:stream'
import { createPrompt } from '../../src/lib/prompt.js'

function makeStreams(inputLines: string[]): { input: PassThrough; output: PassThrough } {
  const input = new PassThrough()
  const output = new PassThrough()
  for (const line of inputLines) {
    input.write(`${line}\n`)
  }
  input.end()
  return { input, output }
}

describe('createPrompt', () => {
  describe('confirm', () => {
    it('returns true for y', async () => {
      const { input, output } = makeStreams(['y'])
      const prompt = createPrompt({ input, output })
      const result = await prompt.confirm('Proceed?')
      expect(result).toBe(true)
    })

    it('returns false for n', async () => {
      const { input, output } = makeStreams(['n'])
      const prompt = createPrompt({ input, output })
      const result = await prompt.confirm('Proceed?')
      expect(result).toBe(false)
    })

    it('uses default value on empty input', async () => {
      const { input, output } = makeStreams([''])
      const prompt = createPrompt({ input, output })
      const result = await prompt.confirm('Proceed?', true)
      expect(result).toBe(true)
    })

    it('reprompts on invalid input then uses default', async () => {
      const { input, output } = makeStreams(['maybe', ''])
      const prompt = createPrompt({ input, output })
      const result = await prompt.confirm('Proceed?', false)
      expect(result).toBe(false)
    })
  })

  describe('multiSelect', () => {
    const options = [
      { id: 'claude-code', label: 'Claude Code', checked: true },
      { id: 'codex', label: 'Codex', checked: false },
      { id: 'opencode', label: 'OpenCode', checked: true }
    ]

    it('returns all ids for "all"', async () => {
      const { input, output } = makeStreams(['all'])
      const prompt = createPrompt({ input, output })
      const result = await prompt.multiSelect('Select harnesses:', options)
      expect(result).toEqual(['claude-code', 'codex', 'opencode'])
    })

    it('returns empty array for "none"', async () => {
      const { input, output } = makeStreams(['none'])
      const prompt = createPrompt({ input, output })
      const result = await prompt.multiSelect('Select harnesses:', options)
      expect(result).toEqual([])
    })

    it('returns checked options on empty input', async () => {
      const { input, output } = makeStreams([''])
      const prompt = createPrompt({ input, output })
      const result = await prompt.multiSelect('Select harnesses:', options)
      expect(result).toEqual(['claude-code', 'opencode'])
    })

    it('selects by comma-separated numbers', async () => {
      const { input, output } = makeStreams(['1,3'])
      const prompt = createPrompt({ input, output })
      const result = await prompt.multiSelect('Select harnesses:', options)
      expect(result).toEqual(['claude-code', 'opencode'])
    })

    it('selects by harness ids', async () => {
      const { input, output } = makeStreams(['codex'])
      const prompt = createPrompt({ input, output })
      const result = await prompt.multiSelect('Select harnesses:', options)
      expect(result).toEqual(['codex'])
    })

    it('reprompts on invalid input', async () => {
      const { input, output } = makeStreams(['invalid', '1'])
      const prompt = createPrompt({ input, output })
      const result = await prompt.multiSelect('Select harnesses:', options)
      expect(result).toEqual(['claude-code'])
    })
  })
})
