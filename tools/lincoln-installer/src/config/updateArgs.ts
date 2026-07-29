import { validateRepoSlug } from '../utils/updateRelease'

export interface UpdateParsedArgs {
  root: string
  repo: string
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

export function parseUpdateArgs(argv: string[]): UpdateParsedArgs {
  const args: UpdateParsedArgs = {
    root: '.',
    repo: 'sushanglewis/Lincoln',
    dryRun: false,
    noTui: false,
    format: 'human',
    help: false,
  }

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]
    switch (arg) {
      case '--root':
        args.root = takeValue(argv, i, '--root')
        i++
        break
      case '--repo':
        args.repo = takeValue(argv, i, '--repo')
        validateRepoSlug(args.repo)
        i++
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
          throw new Error(`Invalid value for --format: ${value}`)
        }
        args.format = value
        i++
        break
      }
      case '--help':
      case '-h':
        args.help = true
        break
      default:
        throw new Error(`Unknown argument: ${arg}`)
    }
  }

  return args
}
