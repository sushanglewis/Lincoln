export interface ParsedArgs {
  command: string
  args: string[]
  flags: Record<string, unknown>
}

/**
 * Flags that never take a value. Boolean flags must not consume the next
 * token, otherwise `lincoln use --yes 1.6.0` would swallow the positional
 * version argument into `flags.yes`.
 */
const BOOLEAN_FLAGS = new Set([
  'yes',
  'y',
  'dry-run',
  'force',
  'check',
  'json',
  'help',
  'h',
  'no-venv',
  'version',
  'v'
])

export function parseArgs(argv: string[]): ParsedArgs {
  const args = argv.slice(2)
  const flags: Record<string, unknown> = {}
  const positional: string[] = []

  for (let i = 0; i < args.length; i++) {
    const arg = args[i]
    if (arg.startsWith('--')) {
      const key = arg.replace(/^--/, '')
      const next = args[i + 1]
      if (!BOOLEAN_FLAGS.has(key) && next && !next.startsWith('-')) {
        flags[key] = next
        i++
      } else {
        flags[key] = true
      }
    } else if (arg.startsWith('-')) {
      const key = arg.replace(/^-/, '')
      const next = args[i + 1]
      if (!BOOLEAN_FLAGS.has(key) && next && !next.startsWith('-')) {
        flags[key] = next
        i++
      } else {
        flags[key] = true
      }
    } else {
      positional.push(arg)
    }
  }

  const command = positional[0] || 'help'
  const validCommands = new Set([
    'install',
    'update',
    'use',
    'doctor',
    'init-project',
    'migrate-project',
    'record',
    'help',
    '--help',
    '-h'
  ])

  if (command === 'help' || command === '--help' || command === '-h') {
    return { command: 'help', args: positional.slice(1), flags }
  }

  if (!validCommands.has(command)) {
    return { command: 'help', args: positional, flags }
  }

  return { command, args: positional.slice(1), flags }
}
