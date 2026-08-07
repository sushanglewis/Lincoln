import type { Readable, Writable } from 'node:stream'

export interface PromptOptions {
  input?: Readable
  output?: Writable
}

export interface MultiSelectOption {
  id: string
  label: string
  checked: boolean
}

export interface Prompt {
  confirm(question: string, defaultValue?: boolean): Promise<boolean>
  multiSelect(question: string, options: ReadonlyArray<MultiSelectOption>): Promise<string[]>
  close(): void
}

interface LineReader {
  readLine(prompt: string): Promise<string>
  close(): void
}

function createLineReader(input: Readable, output: Writable): LineReader {
  const buffer: string[] = []
  const queue: Array<{ resolve: (line: string) => void; reject: (err: Error) => void }> = []
  let remainder = ''
  let ended = false

  function flushQueue(): void {
    while (queue.length > 0 && buffer.length > 0) {
      const next = queue.shift()
      const line = buffer.shift()
      if (next && line !== undefined) {
        next.resolve(line)
      }
    }
  }

  input.on('data', (chunk: Buffer | string) => {
    const text = remainder + chunk.toString('utf-8')
    const lines = text.split('\n')
    remainder = lines.pop() ?? ''
    for (const line of lines) {
      buffer.push(line.replace(/\r$/, ''))
    }
    flushQueue()
  })

  input.on('end', () => {
    ended = true
    if (remainder.length > 0) {
      buffer.push(remainder.replace(/\r$/, ''))
      remainder = ''
    }
    flushQueue()
    while (queue.length > 0) {
      const next = queue.shift()
      next?.resolve('')
    }
  })

  input.on('error', (err) => {
    while (queue.length > 0) {
      queue.shift()?.reject(err)
    }
  })

  return {
    readLine(prompt: string): Promise<string> {
      output.write(prompt)
      if (buffer.length > 0) {
        return Promise.resolve(buffer.shift() ?? '')
      }
      if (ended) {
        return Promise.resolve('')
      }
      return new Promise<string>((resolve, reject) => {
        queue.push({ resolve, reject })
      })
    },
    close(): void {
      // nothing to close for raw streams
    }
  }
}

function normalizeAnswer(text: string): string {
  return text.trim().toLowerCase()
}

export function createPrompt(streams: PromptOptions = {}): Prompt {
  const input = streams.input ?? process.stdin
  const output = streams.output ?? process.stdout
  const reader = createLineReader(input, output)

  async function ask(question: string): Promise<string> {
    return reader.readLine(question)
  }

  return {
    async confirm(question: string, defaultValue = true): Promise<boolean> {
      const hint = defaultValue ? '[Y/n]' : '[y/N]'
      const first = await ask(`${question} ${hint} `)
      const normalized = normalizeAnswer(first)
      if (normalized === 'y' || normalized === 'yes') {
        return true
      }
      if (normalized === 'n' || normalized === 'no') {
        return false
      }
      if (normalized === '') {
        return defaultValue
      }
      const second = await ask('Please answer y or n: ')
      const secondNormalized = normalizeAnswer(second)
      if (secondNormalized === 'y' || secondNormalized === 'yes') {
        return true
      }
      if (secondNormalized === 'n' || secondNormalized === 'no') {
        return false
      }
      return defaultValue
    },

    async multiSelect(
      question: string,
      options: ReadonlyArray<MultiSelectOption>
    ): Promise<string[]> {
      const lines = options.map((opt, index) => {
        const mark = opt.checked ? 'x' : ' '
        return `  [${mark}] ${index + 1}. ${opt.label}`
      })
      const promptText = `${question}\n${lines.join('\n')}\nEnter numbers (e.g. 1,3), 'all', 'none', or harness names: `

      async function parse(answer: string): Promise<string[] | undefined> {
        const normalized = normalizeAnswer(answer)
        if (normalized === 'all') {
          return options.map((opt) => opt.id)
        }
        if (normalized === 'none') {
          return []
        }
        if (normalized === '') {
          return options.filter((opt) => opt.checked).map((opt) => opt.id)
        }
        const parts = normalized.split(/[,\s]+/).filter((part) => part.length > 0)
        const selected = new Set<string>()
        for (const part of parts) {
          const index = Number(part)
          if (!Number.isNaN(index) && index >= 1 && index <= options.length) {
            selected.add(options[index - 1].id)
            continue
          }
          const match = options.find((opt) => opt.id === part)
          if (match) {
            selected.add(match.id)
            continue
          }
          return undefined
        }
        return Array.from(selected)
      }

      let result = await parse(await ask(promptText))
      if (result !== undefined) {
        return result
      }
      const retry = await ask('Invalid selection. Please try again: ')
      result = await parse(retry)
      return result ?? []
    },

    close(): void {
      reader.close()
    }
  }
}
