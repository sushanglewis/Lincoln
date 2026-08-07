import type { SyncReport } from './syncClaude.js'
import { syncClaudeCode } from './syncClaude.js'
import type { HarnessId } from './harnessDetect.js'
import type { LincolnPaths } from './paths.js'
import { runHarnessAdapter } from './runHarnessAdapter.js'

export interface SyncHarnessesOptions {
  harnesses: HarnessId[]
  payloadRoot: string
  paths: LincolnPaths
  projectDir: string
  version: string
  dryRun: boolean
  pythonPath?: string
  syncClaude?: (opts: {
    payloadRoot: string
    targetDir: string
    version: string
    dryRun: boolean
  }) => SyncReport
}

export type HarnessSyncReport = Record<HarnessId, SyncReport>

function emptyReport(): SyncReport {
  return {
    written: [],
    skipped: [],
    preserved: [],
    warnings: []
  }
}

export async function syncHarnesses(opts: SyncHarnessesOptions): Promise<HarnessSyncReport> {
  const reports: HarnessSyncReport = {} as HarnessSyncReport
  const syncClaude = opts.syncClaude ?? syncClaudeCode

  for (const harnessId of opts.harnesses) {
    reports[harnessId] = await syncHarness(harnessId, opts, syncClaude)
  }

  return reports
}

async function syncHarness(
  harnessId: HarnessId,
  opts: SyncHarnessesOptions,
  syncClaude: NonNullable<SyncHarnessesOptions['syncClaude']>
): Promise<SyncReport> {
  if (harnessId === 'claude-code') {
    return syncClaude({
      payloadRoot: opts.payloadRoot,
      targetDir: opts.paths.claudeDir,
      version: opts.version,
      dryRun: opts.dryRun
    })
  }

  if (harnessId === 'codex' || harnessId === 'opencode') {
    if (opts.dryRun) {
      const report = emptyReport()
      report.written.push(`${harnessId} (dry run)`)
      return report
    }
    if (!opts.pythonPath) {
      const report = emptyReport()
      report.warnings.push(
        `Skipped ${harnessId} sync because Python is not available. Install Python 3.10+ or run without --no-venv.`
      )
      return report
    }
    return runHarnessAdapter({
      harnessId,
      payloadRoot: opts.payloadRoot,
      projectDir: opts.projectDir,
      homeDir: opts.paths.homeDir,
      pythonPath: opts.pythonPath,
      dryRun: opts.dryRun
    })
  }

  const report = emptyReport()
  report.warnings.push(`Unsupported harness: ${harnessId}`)
  return report
}
