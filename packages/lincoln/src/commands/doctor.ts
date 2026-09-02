import fs from 'node:fs'
import path from 'node:path'
import { spawn } from 'node:child_process'
import type { LincolnPaths } from '../lib/paths.js'
import { resolveLincolnPaths } from '../lib/paths.js'
import { readVersionMarker } from '../lib/versionMarker.js'
import { isLincolnHookCommand } from '../lib/syncClaude.js'

export interface DoctorCheck {
  name: string
  status: 'ok' | 'warn' | 'skip' | 'error'
  message: string
}

export interface DoctorOptions {
  json?: boolean
}

export interface DoctorDeps {
  paths: LincolnPaths
  nodeVersion: () => string
  pythonVersion: () => Promise<string | undefined>
  pyyamlVersion: () => Promise<string | undefined>
  npmVersion: () => Promise<string | undefined>
  projectRoot: string
}

export interface DoctorResult {
  code: number
  checks: DoctorCheck[]
}

const MIN_NODE_MAJOR = 20
const MIN_PYTHON_MAJOR = 3
const MIN_PYTHON_MINOR = 10

export function createDefaultDeps(): DoctorDeps {
  const paths = resolveLincolnPaths()
  const pythonCommand = resolvePythonCommand(paths)
  return {
    paths,
    nodeVersion: () => process.version,
    pythonVersion: () => queryCommandVersion(pythonCommand, ['--version']),
    pyyamlVersion: () => queryPyyamlVersion(pythonCommand),
    npmVersion: () => queryCommandVersion('npm', ['--version']),
    projectRoot: process.cwd()
  }
}

export async function doctor(
  options: DoctorOptions = {},
  deps: DoctorDeps = createDefaultDeps()
): Promise<DoctorResult> {
  const checks: DoctorCheck[] = []

  checks.push(checkNode(deps.nodeVersion()))
  checks.push(await checkPython(deps.pythonVersion))
  checks.push(await checkPyyaml(deps.pyyamlVersion))
  checks.push(await checkNpm(deps.npmVersion))
  checks.push(checkGlobalMarker(deps.paths))
  checks.push(checkPayloadHooks(deps.paths))
  checks.push(checkSettingsHooks(deps.paths))
  checks.push(checkVenv(deps.paths))
  checks.push(checkProjectMarker(deps.projectRoot))

  const hasError = checks.some((c) => c.status === 'error')
  const result: DoctorResult = { code: hasError ? 1 : 0, checks }

  if (options.json) {
    console.log(JSON.stringify({ checks }, null, 2))
  } else {
    for (const check of checks) {
      const icon = check.status === 'ok' ? '✓' : check.status === 'error' ? '✗' : check.status === 'warn' ? '!' : '-'
      console.log(`${icon} ${check.name}: ${check.message}`)
    }
    if (hasError) {
      console.error('\nOne or more checks failed.')
    }
  }

  return result
}

function checkNode(version: string): DoctorCheck {
  const major = parseNodeMajor(version)
  if (major === undefined) {
    return { name: 'node', status: 'warn', message: `Could not parse Node version: ${version}` }
  }
  if (major < MIN_NODE_MAJOR) {
    return { name: 'node', status: 'error', message: `Node ${version} is below the minimum required v${MIN_NODE_MAJOR}` }
  }
  return { name: 'node', status: 'ok', message: `Node ${version}` }
}

async function checkPython(query: () => Promise<string | undefined>): Promise<DoctorCheck> {
  const version = (await query())?.trim()
  if (!version) {
    return { name: 'python', status: 'error', message: 'Python 3 is not available' }
  }
  const parsed = parsePythonVersion(version)
  if (!parsed) {
    return { name: 'python', status: 'warn', message: `Could not parse Python version: ${version}` }
  }
  if (parsed.major < MIN_PYTHON_MAJOR || (parsed.major === MIN_PYTHON_MAJOR && parsed.minor < MIN_PYTHON_MINOR)) {
    return {
      name: 'python',
      status: 'error',
      message: `Python ${version} is below the minimum required ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}`
    }
  }
  const display = version.replace(/^Python\s+/, '')
  return { name: 'python', status: 'ok', message: `Python ${display}` }
}

async function checkPyyaml(query: () => Promise<string | undefined>): Promise<DoctorCheck> {
  const version = await query()
  if (!version) {
    return { name: 'pyyaml', status: 'error', message: 'PyYAML is not installed for Python 3' }
  }
  return { name: 'pyyaml', status: 'ok', message: `PyYAML ${version}` }
}

async function checkNpm(query: () => Promise<string | undefined>): Promise<DoctorCheck> {
  const version = await query()
  if (!version) {
    return { name: 'npm', status: 'warn', message: 'npm is not available' }
  }
  return { name: 'npm', status: 'ok', message: `npm ${version}` }
}

function checkGlobalMarker(paths: LincolnPaths): DoctorCheck {
  const marker = readVersionMarker(paths)
  if (!marker) {
    return { name: 'global-marker', status: 'warn', message: `No version marker at ${paths.versionMarker}` }
  }
  return { name: 'global-marker', status: 'ok', message: `Lincoln ${marker.version} installed` }
}

function checkPayloadHooks(paths: LincolnPaths): DoctorCheck {
  const hooksDir = path.join(paths.currentDir, '.claude', 'hooks')
  if (!fs.existsSync(hooksDir)) {
    return { name: 'payload-hooks', status: 'warn', message: `Payload hooks not found at ${hooksDir}` }
  }
  const required = ['on-session-start.sh']
  const missing = required.filter((f) => !fs.existsSync(path.join(hooksDir, f)))
  if (missing.length > 0) {
    return { name: 'payload-hooks', status: 'warn', message: `Missing hooks: ${missing.join(', ')}` }
  }
  return { name: 'payload-hooks', status: 'ok', message: `Payload hooks present at ${hooksDir}` }
}

function checkSettingsHooks(paths: LincolnPaths): DoctorCheck {
  const settingsPath = path.join(paths.claudeDir, 'settings.json')
  if (!fs.existsSync(settingsPath)) {
    return { name: 'settings-hooks', status: 'warn', message: `No ~/.claude/settings.json found` }
  }
  let settings: Record<string, unknown>
  try {
    settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8')) as Record<string, unknown>
  } catch (err) {
    return {
      name: 'settings-hooks',
      status: 'error',
      message: `Failed to parse ${settingsPath}: ${err instanceof Error ? err.message : String(err)}`
    }
  }
  const hooks = settings.hooks
  if (hooks === undefined || hooks === null) {
    return { name: 'settings-hooks', status: 'warn', message: 'No hooks key in ~/.claude/settings.json' }
  }
  if (typeof hooks !== 'object') {
    return { name: 'settings-hooks', status: 'error', message: 'hooks key is not an object' }
  }
  const requiredEvents = ['SessionStart', 'PreToolUse', 'PostToolUse', 'Stop']
  const missingEvents: string[] = []
  const malformedEvents: string[] = []
  for (const eventName of requiredEvents) {
    const eventHooks = (hooks as Record<string, unknown>)[eventName]
    if (eventHooks === undefined) {
      missingEvents.push(eventName)
      continue
    }
    if (!Array.isArray(eventHooks)) {
      malformedEvents.push(`${eventName} (not an array)`)
      continue
    }
    let hasLincolnHook = false
    for (const entry of eventHooks) {
      if (typeof entry === 'object' && entry !== null) {
        const innerHooks = (entry as Record<string, unknown>).hooks
        if (Array.isArray(innerHooks)) {
          for (const h of innerHooks) {
            if (
              typeof h === 'object' &&
              h !== null &&
              (h as Record<string, unknown>).type === 'command' &&
              typeof (h as Record<string, unknown>).command === 'string' &&
              isLincolnHookCommand((h as Record<string, unknown>).command as string)
            ) {
              hasLincolnHook = true
              break
            }
          }
        }
      }
      if (hasLincolnHook) break
    }
    if (!hasLincolnHook) {
      malformedEvents.push(`${eventName} (no Lincoln hook)`)
    }
  }
  if (missingEvents.length > 0 || malformedEvents.length > 0) {
    const parts: string[] = []
    if (missingEvents.length > 0) parts.push(`missing: ${missingEvents.join(', ')}`)
    if (malformedEvents.length > 0) parts.push(`malformed: ${malformedEvents.join(', ')}`)
    return { name: 'settings-hooks', status: 'error', message: parts.join('; ') }
  }
  return { name: 'settings-hooks', status: 'ok', message: 'Lincoln hooks registered in ~/.claude/settings.json' }
}

function checkVenv(paths: LincolnPaths): DoctorCheck {
  if (!fs.existsSync(paths.venvDir)) {
    return { name: 'venv', status: 'warn', message: `Virtual environment not found at ${paths.venvDir}` }
  }
  const pythonExe = path.join(paths.venvDir, process.platform === 'win32' ? 'Scripts' : 'bin', 'python')
  if (!fs.existsSync(pythonExe)) {
    return { name: 'venv', status: 'warn', message: `Virtual environment exists but python executable is missing` }
  }
  return { name: 'venv', status: 'ok', message: `Virtual environment present at ${paths.venvDir}` }
}

function checkProjectMarker(projectRoot: string): DoctorCheck {
  const markerPath = path.join(projectRoot, '.lincoln.yaml')
  if (!fs.existsSync(markerPath)) {
    return { name: 'project-marker', status: 'skip', message: `No .lincoln.yaml in ${projectRoot}` }
  }
  return { name: 'project-marker', status: 'ok', message: `Project marker found at ${markerPath}` }
}

function resolvePythonCommand(paths: LincolnPaths): string {
  const venvPython = path.join(
    paths.venvDir,
    process.platform === 'win32' ? 'Scripts' : 'bin',
    process.platform === 'win32' ? 'python.exe' : 'python'
  )
  if (fs.existsSync(venvPython)) {
    return venvPython
  }
  return 'python3'
}

function parseNodeMajor(version: string): number | undefined {
  const match = /^v?(\d+)/.exec(version)
  if (!match) {
    return undefined
  }
  return Number(match[1])
}

function parsePythonVersion(version: string): { major: number; minor: number } | undefined {
  const match = /(\d+)\.(\d+)/.exec(version)
  if (!match) {
    return undefined
  }
  return { major: Number(match[1]), minor: Number(match[2]) }
}

async function queryCommandVersion(command: string, args: string[]): Promise<string | undefined> {
  return new Promise((resolvePromise) => {
    const child = spawn(command, args, {
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

async function queryPyyamlVersion(pythonCommand: string): Promise<string | undefined> {
  return new Promise((resolvePromise) => {
    const child = spawn(
      pythonCommand,
      ['-c', 'import yaml; print(yaml.__version__)'],
      { stdio: ['ignore', 'pipe', 'ignore'], shell: process.platform === 'win32' }
    )
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
