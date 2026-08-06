import fs from 'node:fs'
import path from 'node:path'
import { spawn } from 'node:child_process'
import type { LincolnPaths } from '../lib/paths.js'
import { resolveLincolnPaths } from '../lib/paths.js'
import { readVersionMarker } from '../lib/versionMarker.js'

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
  return {
    paths: resolveLincolnPaths(),
    nodeVersion: () => process.version,
    pythonVersion: () => queryCommandVersion('python3', ['--version']),
    pyyamlVersion: () => queryPyyamlVersion(),
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
  const version = await query()
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
  return { name: 'python', status: 'ok', message: `Python ${version}` }
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

function parseNodeMajor(version: string): number | undefined {
  const match = /^v?(\d+)/.exec(version)
  if (!match) {
    return undefined
  }
  return Number(match[1])
}

function parsePythonVersion(version: string): { major: number; minor: number } | undefined {
  const match = /^(\d+)\.(\d+)/.exec(version)
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

async function queryPyyamlVersion(): Promise<string | undefined> {
  return new Promise((resolvePromise) => {
    const child = spawn(
      'python3',
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
