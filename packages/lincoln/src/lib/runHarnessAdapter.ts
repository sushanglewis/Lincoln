import { spawn, type ChildProcess, type SpawnOptions } from 'node:child_process'
import type { SyncReport } from './syncClaude.js'

export interface RunHarnessAdapterOptions {
  harnessId: 'codex' | 'opencode'
  payloadRoot: string
  projectDir: string
  homeDir: string
  pythonPath: string
  dryRun: boolean
  spawnCommand?: SpawnCommand
}

type SpawnCommand = (command: string, args: string[], options?: SpawnOptions) => ChildProcess

function runCommand(
  command: string,
  args: string[],
  spawnCommand: SpawnCommand
): Promise<number | null> {
  return new Promise((resolvePromise, rejectPromise) => {
    const child = spawnCommand(command, args, { stdio: 'inherit' })
    child.on('close', (code) => {
      resolvePromise(code)
    })
    child.on('error', (err) => {
      rejectPromise(err)
    })
  })
}

export async function runHarnessAdapter(opts: RunHarnessAdapterOptions): Promise<SyncReport> {
  const report: SyncReport = {
    written: [],
    skipped: [],
    preserved: [],
    warnings: []
  }

  if (opts.dryRun) {
    report.written.push(`${opts.harnessId} (dry run)`)
    return report
  }

  const args = [
    `${opts.payloadRoot}/scripts/lincoln_harness_adapter.py`,
    '--harness',
    opts.harnessId,
    '--root',
    opts.payloadRoot,
    '--project-dir',
    opts.projectDir,
    '--home-dir',
    opts.homeDir
  ]

  try {
    const spawnCommand = (opts.spawnCommand ?? spawn) as SpawnCommand
    const code = await runCommand(opts.pythonPath, args, spawnCommand)
    if (code === 0) {
      report.written.push(opts.harnessId)
    } else {
      report.warnings.push(
        `Adapter for ${opts.harnessId} exited with code ${code}. Run manually to diagnose.`
      )
    }
  } catch (err) {
    report.warnings.push(
      `Failed to run adapter for ${opts.harnessId}: ${err instanceof Error ? err.message : String(err)}`
    )
  }

  return report
}
