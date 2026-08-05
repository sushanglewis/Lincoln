import { parseArgs } from './cli.js'
import { install } from './commands/install.js'

const USAGE = `Lincoln — Global agent harness plugin CLI

Usage:
  lincoln <command> [options]

Commands:
  install          One-time global setup: sync to ~/.claude/, ~/.codex/, ~/.opencode/
  update           Pull latest release and re-sync globally
  use <version>   Switch active global version
  doctor           Diagnose harness integration
  init-project     Create .lincoln.yaml in current project
  migrate-project  Remove vendored framework files from an existing project
  record           Launch the Lincoln interview recorder TUI
  help             Show this help message

Options:
  --yes, -y        Skip confirmation prompts
  --dry-run        Show what would be done without making changes
  --force          Force re-install even if up to date
  --json           Output machine-readable JSON (where supported)
  --help, -h       Show this help message
`

export async function main(argv: string[]): Promise<number> {
  const parsed = parseArgs(argv)

  if (parsed.command === 'help') {
    console.log(USAGE)
    return 0
  }

  if (parsed.command === 'install') {
    return install({
      yes: Boolean(parsed.flags.yes || parsed.flags.y),
      dryRun: Boolean(parsed.flags['dry-run']),
      force: Boolean(parsed.flags.force),
      harnesses: parsed.args,
      noVenv: Boolean(parsed.flags['no-venv'])
    })
  }

  console.log(USAGE)
  return 0
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main(process.argv).then((code) => process.exit(code))
}
