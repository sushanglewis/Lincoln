export interface ParsedArgs {
  root: string
  harness: string[]
  yes: boolean
  dryRun: boolean
  noTui: boolean
  format: 'human' | 'json'
  help: boolean
}

function takeValue(argv: string[], i: number, name: string): string {
  const value = argv[i + 1]
  if (value === undefined || value.startsWith('--')) {
    throw new Error(`Missing value for ${name}`)
  }
  return value
}

export function parseArgs(argv: string[]): ParsedArgs {
  const args: ParsedArgs = {
    root: '.',
    harness: [],
    yes: false,
    dryRun: false,
    noTui: false,
    format: 'human',
    help: false,
  }

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]
    switch (arg) {
      case '--root': {
        const value = takeValue(argv, i, '--root')
        args.root = value
        i++
        break
      }
      case '--harness': {
        const value = takeValue(argv, i, '--harness')
        args.harness.push(value)
        i++
        break
      }
      case '--yes':
        args.yes = true
        break
      case '--dry-run':
        args.dryRun = true
        break
      case '--no-tui':
        args.noTui = true
        break
      case '--format': {
        const value = takeValue(argv, i, '--format')
        if (value !== 'human' && value !== 'json') {
          throw new Error(`Invalid value for --format: ${value}. Must be 'human' or 'json'.`)
        }
        args.format = value
        i++
        break
      }
      case '-h':
      case '--help':
        args.help = true
        break
      default:
        if (arg.startsWith('--')) {
          throw new Error(`Unknown argument: ${arg}`)
        }
        break
    }
  }

  return args
}
