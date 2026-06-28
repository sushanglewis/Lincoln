import { parseArgs as nodeParseArgs } from 'node:util'

export interface ParsedArgs {
  topic?: string
  designId?: string
  branch?: string
  sessionId?: string
  noTui: boolean
  help: boolean
}

export function parseArgs(argv: string[]): ParsedArgs {
  const { values } = nodeParseArgs({
    args: argv,
    options: {
      topic: { type: 'string' },
      'design-id': { type: 'string' },
      branch: { type: 'string' },
      'session-id': { type: 'string' },
      'no-tui': { type: 'boolean', default: false },
      help: { type: 'boolean', short: 'h', default: false },
    },
    strict: false,
    allowPositionals: true,
  })

  return {
    topic: values.topic as string | undefined,
    designId: values['design-id'] as string | undefined,
    branch: values.branch as string | undefined,
    sessionId: values['session-id'] as string | undefined,
    noTui: values['no-tui'] as boolean,
    help: values.help as boolean,
  }
}
