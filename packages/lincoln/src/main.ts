import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { parseArgs } from './cli.js'
import { doctor } from './commands/doctor.js'
import { initProject } from './commands/initProject.js'
import { install } from './commands/install.js'
import { update } from './commands/update.js'
import { use } from './commands/use.js'
import { migrateProject } from './commands/migrateProject.js'
import { record } from './commands/record.js'
import { readLocalPackageVersion } from './lib/packageInfo.js'

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
  --harnesses      Comma-separated harness ids (claude-code, codex, opencode)
  --no-interactive Never prompt; fail if --yes is also missing
  --check          Check for available updates without installing (update)
  --json           Output machine-readable JSON (where supported)
  --help, -h       Show this help message
  --version, -v    Show the installed Lincoln version
`

export async function main(argv: string[]): Promise<number> {
  const parsed = parseArgs(argv)

  if (parsed.flags.version || parsed.flags.v) {
    const version = readLocalPackageVersion()
    console.log(version ? `Lincoln ${version}` : 'Lincoln (unknown version)')
    return 0
  }

  if (parsed.command === 'help') {
    console.log(USAGE)
    return 0
  }

  if (parsed.command === 'install') {
    const harnessesFlag = typeof parsed.flags.harnesses === 'string'
      ? String(parsed.flags.harnesses).split(',').map((id) => id.trim()).filter((id) => id.length > 0)
      : []
    const harnesses = harnessesFlag.length > 0 ? harnessesFlag : parsed.args
    return install({
      yes: Boolean(parsed.flags.yes || parsed.flags.y),
      dryRun: Boolean(parsed.flags['dry-run']),
      force: Boolean(parsed.flags.force),
      harnesses,
      noVenv: Boolean(parsed.flags['no-venv']),
      noInteractive: Boolean(parsed.flags['no-interactive'])
    })
  }

  if (parsed.command === 'update') {
    return update({
      check: Boolean(parsed.flags.check),
      dryRun: Boolean(parsed.flags['dry-run']),
      yes: Boolean(parsed.flags.yes || parsed.flags.y)
    })
  }

  if (parsed.command === 'use') {
    const version = parsed.args[0]
    if (!version) {
      console.error('Usage: lincoln use <version> [--yes] [--dry-run]')
      return 1
    }
    return use(version, {
      dryRun: Boolean(parsed.flags['dry-run']),
      yes: Boolean(parsed.flags.yes || parsed.flags.y)
    })
  }

  if (parsed.command === 'doctor') {
    const result = await doctor({ json: Boolean(parsed.flags.json) })
    return result.code
  }

  if (parsed.command === 'init-project') {
    return initProject(process.cwd(), {
      force: Boolean(parsed.flags.force),
      dryRun: Boolean(parsed.flags['dry-run'])
    })
  }

  if (parsed.command === 'migrate-project') {
    return migrateProject(process.cwd(), {
      dryRun: Boolean(parsed.flags['dry-run']),
      yes: Boolean(parsed.flags.yes || parsed.flags.y),
      force: Boolean(parsed.flags.force)
    })
  }

  if (parsed.command === 'record') {
    return record(parsed.args)
  }

  console.log(USAGE)
  return 0
}

if (
  process.argv[1] &&
  path.resolve(fs.realpathSync(fileURLToPath(import.meta.url))) ===
    path.resolve(fs.realpathSync(process.argv[1]))
) {
  main(process.argv)
    .then((code) => process.exit(code))
    .catch((err) => {
      console.error(err instanceof Error ? err.message : String(err))
      process.exit(1)
    })
}
