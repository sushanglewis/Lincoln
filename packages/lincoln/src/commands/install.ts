import fs from 'node:fs'
import path from 'node:path'
import { spawn } from 'node:child_process'
import type { LincolnPaths } from '../lib/paths.js'
import { resolveLincolnPaths } from '../lib/paths.js'
import { writeVersionMarker } from '../lib/versionMarker.js'
import { readLocalPackageVersion, resolvePayloadRoot } from '../lib/packageInfo.js'
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
  payloadRoot: string
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
    payloadRoot: resolvePayloadRoot() || '',
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

  const payloadRoot = deps.payloadRoot
  if (!payloadRoot || !fs.existsSync(payloadRoot)) {
    console.error(
      `Lincoln payload not found. Run "npm install -g @sushanglewis/lincoln" first.`
    )
    return 1
  }

  const versionDir = path.join(deps.paths.versionsDir, version)
  if (!options.dryRun) {
    fs.mkdirSync(versionDir, { recursive: true })
    fs.cpSync(payloadRoot, versionDir, { recursive: true, force: true })
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

  if (!options.dryRun && !options.noVenv) {
    await setupVenv(deps.paths, payloadRoot)
  }

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

function runCommand(command: string, args: string[]): Promise<number> {
  return new Promise((resolvePromise, rejectPromise) => {
    const child = spawn(command, args, { stdio: 'inherit' })
    child.on('close', (code) => resolvePromise(code ?? 1))
    child.on('error', (err) => rejectPromise(err))
  })
}

function pythonCommand(): string {
  return process.env.LINCOLN_PYTHON || 'python3'
}

async function setupVenv(paths: LincolnPaths, payloadRoot: string): Promise<void> {
  const pythonExe = path.join(
    paths.venvDir,
    process.platform === 'win32' ? 'Scripts' : 'bin',
    process.platform === 'win32' ? 'python.exe' : 'python'
  )

  if (!fs.existsSync(pythonExe)) {
    console.log('Creating Lincoln virtual environment...')
    await runCommand(pythonCommand(), ['-m', 'venv', paths.venvDir])
  }

  const requirementsPath = path.join(payloadRoot, 'requirements.txt')
  if (fs.existsSync(requirementsPath)) {
    console.log('Installing Python dependencies...')
    const pipExe = path.join(
      paths.venvDir,
      process.platform === 'win32' ? 'Scripts' : 'bin',
      process.platform === 'win32' ? 'pip.exe' : 'pip'
    )
    await runCommand(pipExe, ['install', '-r', requirementsPath])
  }
}
