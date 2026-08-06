import fs from 'node:fs'
import path from 'node:path'
import { spawn } from 'node:child_process'
import type { LincolnPaths } from '../lib/paths.js'
import { resolveLincolnPaths } from '../lib/paths.js'
import { writeVersionMarker } from '../lib/versionMarker.js'
import { readLocalPackageVersion, resolvePayloadRoot } from '../lib/packageInfo.js'
import type { HarnessSyncReport, SyncHarnessesOptions } from '../lib/syncHarness.js'
import { syncHarnesses } from '../lib/syncHarness.js'
import { detectGlobalHarnesses, installedHarnessIds, isValidHarnessId, HARNESS_IDS } from '../lib/harnessDetect.js'
import type { HarnessId } from '../lib/harnessDetect.js'
import { buildHarnessOptions, resolveHarnessSelection } from '../lib/harnessSelect.js'
import { createPrompt } from '../lib/prompt.js'
import type { Prompt } from '../lib/prompt.js'

export interface InstallOptions {
  yes: boolean
  dryRun: boolean
  force: boolean
  harnesses: string[]
  noVenv: boolean
  noInteractive: boolean
}

export interface InstallDeps {
  paths: LincolnPaths
  payloadRoot: string
  syncHarnesses: (opts: SyncHarnessesOptions) => Promise<HarnessSyncReport>
  createPrompt: () => Prompt
  resolvePythonForVenv: (
    envOverride?: string,
    candidates?: string[],
    queryVersion?: (cmd: string) => Promise<string | undefined>
  ) => Promise<string | undefined>
  isTTY: boolean
}

export function createDefaultDeps(): InstallDeps {
  return {
    paths: resolveLincolnPaths(),
    payloadRoot: resolvePayloadRoot() || '',
    syncHarnesses,
    createPrompt,
    resolvePythonForVenv,
    isTTY: Boolean(process.stdin.isTTY && process.stdout.isTTY)
  }
}

export async function install(
  options: InstallOptions,
  deps: InstallDeps = createDefaultDeps()
): Promise<number> {
  const version = readLocalPackageVersion()
  if (!version) {
    console.error('Could not determine Lincoln version')
    return 1
  }

  const payloadRoot = deps.payloadRoot
  if (!payloadRoot || !fs.existsSync(payloadRoot)) {
    console.error('Lincoln payload not found. Run "npm install -g @sushanglewis/lincoln" first.')
    return 1
  }

  if (!options.dryRun && !options.yes && (options.noInteractive || !deps.isTTY)) {
    console.error(
      'This will install Lincoln globally. Run with --yes to proceed, or run interactively in a TTY.'
    )
    return 1
  }

  const harnesses = await resolveHarnesses(options, deps)
  if (harnesses.length === 0) {
    return 1
  }

  const pythonPath = await resolvePythonIfNeeded(options, deps, harnesses)
  if (pythonPath === null) {
    return 1
  }

  if (!options.dryRun) {
    const versionDir = path.join(deps.paths.versionsDir, version)
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

  const reports = await deps.syncHarnesses({
    harnesses,
    payloadRoot: deps.paths.currentDir,
    paths: deps.paths,
    projectDir: deps.paths.lincolnHome,
    version,
    dryRun: options.dryRun,
    pythonPath
  })

  if (!options.dryRun) {
    writeVersionMarker(deps.paths, {
      version,
      installedAt: new Date().toISOString(),
      harnesses,
      managedFiles: collectManagedFiles(reports)
    })
  }

  printSummary(options, version, harnesses, reports)
  return 0
}

async function resolvePythonIfNeeded(
  options: InstallOptions,
  deps: InstallDeps,
  harnesses: HarnessId[]
): Promise<string | undefined | null> {
  const needsPython =
    !options.dryRun && !options.noVenv && harnesses.some((id) => id === 'codex' || id === 'opencode')
  if (!needsPython) {
    return undefined
  }

  const pythonCommand = await deps.resolvePythonForVenv()
  if (!pythonCommand) {
    console.error(
      'Python 3.10+ is required for Codex/OpenCode sync but was not found. Set LINCOLN_PYTHON to a compatible Python executable, or run with --no-venv.'
    )
    return null
  }

  await setupVenv(deps.paths, deps.payloadRoot, pythonCommand)
  return venvPythonPath(deps.paths)
}

async function resolveHarnesses(options: InstallOptions, deps: InstallDeps): Promise<HarnessId[]> {
  const detected = detectGlobalHarnesses(deps.paths.homeDir)

  if (options.harnesses.length > 0) {
    const invalid = options.harnesses.filter((id) => !isValidHarnessId(id))
    if (invalid.length > 0) {
      console.error(`Unknown harness id(s): ${invalid.join(', ')}`)
      console.error(`Valid ids: ${HARNESS_IDS.join(', ')}`)
      return []
    }
    return options.harnesses as HarnessId[]
  }

  const selected = installedHarnessIds(deps.paths.homeDir)
  if (selected.length > 0 && !options.dryRun && !options.yes && !options.noInteractive && deps.isTTY) {
    const prompt = deps.createPrompt()
    try {
      const answer = await prompt.multiSelect(
        'Select agent harnesses to install Lincoln into:',
        buildHarnessOptions(detected)
      )
      const resolved = resolveHarnessSelection(detected, answer)
      if (resolved.length === 0) {
        console.error('No harnesses selected. Aborting.')
        return []
      }
      return resolved
    } catch (err) {
      console.error(`Interactive selection failed: ${err instanceof Error ? err.message : String(err)}`)
      return []
    } finally {
      prompt.close()
    }
  }

  if (selected.length === 0 && !options.dryRun) {
    console.error('No agent harness detected. Install Claude Code, Codex, or OpenCode first.')
    return []
  }

  return selected
}

function collectManagedFiles(reports: HarnessSyncReport): string[] {
  const files: string[] = []
  for (const report of Object.values(reports)) {
    files.push(...report.written, ...report.skipped, ...report.preserved)
  }
  return files
}

function printSummary(
  options: InstallOptions,
  version: string,
  harnesses: HarnessId[],
  reports: HarnessSyncReport
): void {
  const warnings = collectWarnings(reports)
  if (options.dryRun) {
    console.log(`Dry run: would install Lincoln ${version} for harnesses: ${harnesses.join(', ')}`)
  } else {
    console.log(`Installed Lincoln ${version} for harnesses: ${harnesses.join(', ')}`)
  }
  for (const [harnessId, report] of Object.entries(reports)) {
    const count = report.written.length + report.skipped.length + report.preserved.length
    console.log(`  ${harnessId}: ${count} file(s)`)
  }
  for (const warning of warnings) {
    console.warn(`  warning: ${warning}`)
  }
}

function collectWarnings(reports: HarnessSyncReport): string[] {
  const warnings: string[] = []
  for (const report of Object.values(reports)) {
    warnings.push(...report.warnings)
  }
  return warnings
}

function runCommand(command: string, args: string[]): Promise<number> {
  return new Promise((resolvePromise, rejectPromise) => {
    const child = spawn(command, args, { stdio: 'inherit' })
    child.on('close', (code) => resolvePromise(code ?? 1))
    child.on('error', (err) => rejectPromise(err))
  })
}

const MIN_PYTHON_MAJOR = 3
const MIN_PYTHON_MINOR = 10
const DEFAULT_PYTHON_CANDIDATES = ['python3.12', 'python3.11', 'python3.10', 'python3']

function parsePythonVersion(version: string): { major: number; minor: number } | undefined {
  const match = /(\d+)\.(\d+)/.exec(version)
  if (!match) {
    return undefined
  }
  return { major: Number(match[1]), minor: Number(match[2]) }
}

async function queryPythonVersion(command: string): Promise<string | undefined> {
  return new Promise((resolvePromise) => {
    const child = spawn(command, ['--version'], {
      stdio: ['ignore', 'pipe', 'ignore'],
      shell: process.platform === 'win32'
    })
    let stdout = ''
    child.stdout?.on('data', (chunk: Buffer | string) => {
      stdout += chunk.toString()
    })
    child.on('close', (code) => {
      const text = stdout.trim()
      resolvePromise(code === 0 && text.length > 0 ? text : undefined)
    })
    child.on('error', () => resolvePromise(undefined))
  })
}

export async function resolvePythonForVenv(
  envOverride: string | undefined = process.env.LINCOLN_PYTHON,
  candidates: string[] = DEFAULT_PYTHON_CANDIDATES,
  queryVersion: (cmd: string) => Promise<string | undefined> = queryPythonVersion
): Promise<string | undefined> {
  const list = envOverride ? [envOverride] : candidates
  for (const cmd of list) {
    const version = await queryVersion(cmd)
    if (!version) {
      continue
    }
    const parsed = parsePythonVersion(version)
    if (
      parsed &&
      parsed.major >= MIN_PYTHON_MAJOR &&
      (parsed.major > MIN_PYTHON_MAJOR || parsed.minor >= MIN_PYTHON_MINOR)
    ) {
      return cmd
    }
  }
  return undefined
}

function venvPythonPath(paths: LincolnPaths): string {
  return path.join(
    paths.venvDir,
    process.platform === 'win32' ? 'Scripts' : 'bin',
    process.platform === 'win32' ? 'python.exe' : 'python'
  )
}

async function setupVenv(paths: LincolnPaths, payloadRoot: string, pythonCommand: string): Promise<void> {
  const pythonExe = venvPythonPath(paths)

  if (!fs.existsSync(pythonExe)) {
    console.log('Creating Lincoln virtual environment...')
    const venvCode = await runCommand(pythonCommand, ['-m', 'venv', paths.venvDir])
    if (venvCode !== 0) {
      throw new Error(`Failed to create virtual environment (exit code ${venvCode})`)
    }
  }

  const requirementsPath = path.join(payloadRoot, 'requirements.txt')
  if (fs.existsSync(requirementsPath)) {
    console.log('Installing Python dependencies...')
    const pipExe = path.join(
      paths.venvDir,
      process.platform === 'win32' ? 'Scripts' : 'bin',
      process.platform === 'win32' ? 'pip.exe' : 'pip'
    )
    const pipCode = await runCommand(pipExe, ['install', '-r', requirementsPath])
    if (pipCode !== 0) {
      throw new Error(`Failed to install Python dependencies (exit code ${pipCode})`)
    }
  }
}
