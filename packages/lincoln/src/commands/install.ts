import fs from 'node:fs'
import path from 'node:path'
import type { LincolnPaths } from '../lib/paths.js'
import { resolveLincolnPaths } from '../lib/paths.js'
import { writeVersionMarker } from '../lib/versionMarker.js'
import { readLocalPackageVersion } from '../lib/packageInfo.js'
import type { SyncReport } from '../lib/syncClaude.js'
import { syncClaudeCode } from '../lib/syncClaude.js'
import { installedHarnessIds } from '../lib/harnessDetect.js'

export interface InstallOptions {
  yes: boolean
  dryRun: boolean
  force: boolean
  harnesses: string[]
  noVenv: boolean
}

export interface InstallDeps {
  paths: LincolnPaths
  syncClaude: (opts: {
    payloadRoot: string
    targetDir: string
    version: string
    dryRun: boolean
  }) => SyncReport
}

export function createDefaultDeps(): InstallDeps {
  return {
    paths: resolveLincolnPaths(),
    syncClaude: syncClaudeCode
  }
}

export async function install(
  options: InstallOptions,
  deps: InstallDeps = createDefaultDeps()
): Promise<number> {
  if (!options.dryRun && !options.yes) {
    console.error('This will install Lincoln globally. Run with --yes to proceed.')
    return 1
  }

  const version = readLocalPackageVersion()
  if (!version) {
    console.error('Could not determine Lincoln version')
    return 1
  }

  const harnesses =
    options.harnesses.length > 0 ? options.harnesses : installedHarnessIds(deps.paths.homeDir)

  if (harnesses.length === 0) {
    console.error('No agent harness detected. Install Claude Code, Codex, or OpenCode first.')
    return 1
  }

  const payloadRoot = deps.paths.currentDir
  if (!fs.existsSync(payloadRoot)) {
    console.error(
      `Lincoln payload not found at ${payloadRoot}. Run "npm install -g @sushanglewis/lincoln" first.`
    )
    return 1
  }

  const versionDir = path.join(deps.paths.versionsDir, version)
  if (!options.dryRun) {
    fs.mkdirSync(versionDir, { recursive: true })
    try {
      fs.rmSync(deps.paths.currentDir, { recursive: true, force: true })
      fs.symlinkSync(versionDir, deps.paths.currentDir)
    } catch {
      fs.rmSync(deps.paths.currentDir, { recursive: true, force: true })
      fs.cpSync(versionDir, deps.paths.currentDir, { recursive: true, force: true })
    }
  }

  const report = deps.syncClaude({
    payloadRoot: deps.paths.currentDir,
    targetDir: deps.paths.claudeDir,
    version,
    dryRun: options.dryRun
  })

  if (!options.dryRun) {
    writeVersionMarker(deps.paths, {
      version,
      installedAt: new Date().toISOString(),
      harnesses,
      managedFiles: report.written
    })
  }

  if (options.dryRun) {
    console.log(`Dry run: would install Lincoln ${version} for harnesses: ${harnesses.join(', ')}`)
    console.log(`Would write ${report.written.length} files`)
  } else {
    console.log(`Installed Lincoln ${version} for harnesses: ${harnesses.join(', ')}`)
    console.log(`Wrote ${report.written.length} files`)
  }

  return 0
}
