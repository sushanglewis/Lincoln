import fs from 'node:fs'
import path from 'node:path'
import { spawn } from 'node:child_process'
import type { LincolnPaths } from '../lib/paths.js'
import { resolveLincolnPaths } from '../lib/paths.js'
import { createRegistryClient } from '../lib/npmRegistry.js'
import { install } from './install.js'
import type { InstallOptions } from './install.js'

const PACKAGE_NAME = '@sushanglewis/lincoln'
const SEMVER_REGEX = /^v?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/
const STRICT_SEMVER_REGEX = /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/
const DIST_TAG_REGEX = /^[a-zA-Z][a-zA-Z0-9._-]*$/

export interface UseOptions {
  dryRun: boolean
  yes: boolean
}

export interface UseDeps {
  paths: LincolnPaths
  resolveVersion: (spec: string) => Promise<string>
  ensureVersionAvailable: (version: string) => Promise<void>
  npmGlobalRoot: () => Promise<string | undefined>
  runInstall: (options: InstallOptions) => Promise<number>
}

export function createDefaultDeps(): UseDeps {
  const paths = resolveLincolnPaths()
  const registry = createRegistryClient()
  return {
    paths,
    resolveVersion: async (spec) => {
      // Exact (optionally v-prefixed) versions resolve locally without a
      // registry round-trip, so switching between installed versions works
      // offline. Dist-tags (latest, next, ...) need the registry.
      const normalized = spec.startsWith('v') ? spec.slice(1) : spec
      if (STRICT_SEMVER_REGEX.test(normalized)) {
        return normalized
      }
      return registry.resolveVersion(PACKAGE_NAME, spec)
    },
    ensureVersionAvailable: async (version) => {
      const code = await runNpmInstallGlobal(PACKAGE_NAME, version)
      if (code !== 0) {
        throw new Error(`npm install -g ${PACKAGE_NAME}@${version} exited with ${code}`)
      }
    },
    npmGlobalRoot: () => runNpmRootGlobal(),
    runInstall: (options) => install(options)
  }
}

export async function use(
  spec: string,
  options: UseOptions,
  deps: Partial<UseDeps> = {}
): Promise<number> {
  if (!isValidVersion(spec)) {
    console.error(`Invalid version: ${spec}`)
    return 1
  }

  const resolved: UseDeps = { ...createDefaultDeps(), ...deps }

  let version: string
  try {
    version = await resolved.resolveVersion(spec)
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    console.error(`Failed to resolve version ${spec}: ${message}`)
    return 1
  }

  const versionDir = path.join(resolved.paths.versionsDir, version)
  const alreadyInstalled = fs.existsSync(versionDir)

  if (options.dryRun) {
    if (alreadyInstalled) {
      console.log(`Dry run: would switch ${resolved.paths.currentDir} to ${versionDir}`)
    } else {
      console.log(
        `Dry run: would install ${PACKAGE_NAME}@${version} globally, then switch ${resolved.paths.currentDir} to ${versionDir}`
      )
    }
    return 0
  }

  if (!options.yes) {
    console.error(`Will switch Lincoln to ${version}. Run with --yes to proceed.`)
    return 1
  }

  if (!alreadyInstalled) {
    try {
      await resolved.ensureVersionAvailable(version)
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      console.error(`Failed to install ${PACKAGE_NAME}@${version}: ${message}`)
      return 1
    }

    if (!fs.existsSync(versionDir)) {
      // `npm install -g` places the package in the npm global root; it does
      // not populate ~/.lincoln/versions. Copy the payload over so the
      // version switch below has a real directory to point at.
      try {
        await copyVersionFromNpmGlobal(resolved, versionDir)
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err)
        console.error(`Failed to populate ${versionDir}: ${message}`)
        return 1
      }
    }

    if (!fs.existsSync(versionDir)) {
      console.error(
        `Provisioning ${PACKAGE_NAME}@${version} did not produce ${versionDir}; cannot switch versions.`
      )
      return 1
    }
  }

  try {
    switchCurrentLink(resolved.paths, versionDir)
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    console.error(`Failed to switch ${resolved.paths.currentDir}: ${message}`)
    return 1
  }

  const syncCode = await resolved.runInstall(defaultInstallOptions())
  if (syncCode !== 0) {
    console.error(`lincoln install failed with exit code ${syncCode}`)
    return 1
  }

  // The trailing install re-points ~/.lincoln/current at the *running* CLI's
  // own version dir (Task 9 behavior, pending the install payload fix).
  // Re-assert the requested version so the switch actually sticks.
  try {
    switchCurrentLink(resolved.paths, versionDir)
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    console.error(`Failed to switch ${resolved.paths.currentDir}: ${message}`)
    return 1
  }

  console.log(`Switched Lincoln to ${version}`)
  return 0
}

function isValidVersion(version: string): boolean {
  return SEMVER_REGEX.test(version) || DIST_TAG_REGEX.test(version)
}

async function copyVersionFromNpmGlobal(deps: UseDeps, versionDir: string): Promise<void> {
  const globalRoot = await deps.npmGlobalRoot()
  if (!globalRoot) {
    return
  }
  const packageRoot = path.join(globalRoot, ...PACKAGE_NAME.split('/'))
  if (!fs.existsSync(packageRoot)) {
    return
  }
  fs.mkdirSync(path.dirname(versionDir), { recursive: true })
  fs.cpSync(packageRoot, versionDir, { recursive: true })
}

function switchCurrentLink(paths: LincolnPaths, versionDir: string): void {
  fs.mkdirSync(paths.lincolnHome, { recursive: true })
  try {
    fs.rmSync(paths.currentDir, { recursive: true, force: true })
    fs.symlinkSync(versionDir, paths.currentDir)
  } catch {
    fs.rmSync(paths.currentDir, { recursive: true, force: true })
    fs.cpSync(versionDir, paths.currentDir, { recursive: true, force: true })
  }
}

function defaultInstallOptions(): InstallOptions {
  return { yes: true, dryRun: false, force: false, harnesses: [], noVenv: true }
}

function runNpmInstallGlobal(packageName: string, version: string): Promise<number> {
  return new Promise((resolvePromise) => {
    const child = spawn('npm', ['install', '-g', `${packageName}@${version}`], {
      stdio: 'inherit',
      shell: process.platform === 'win32'
    })
    child.on('close', (code) => resolvePromise(code ?? 1))
    child.on('error', () => resolvePromise(1))
  })
}

function runNpmRootGlobal(): Promise<string | undefined> {
  return new Promise((resolvePromise) => {
    const child = spawn('npm', ['root', '-g'], {
      stdio: ['ignore', 'pipe', 'ignore'],
      shell: process.platform === 'win32'
    })
    let stdout = ''
    child.stdout?.on('data', (chunk: Buffer | string) => {
      stdout += chunk.toString()
    })
    child.on('close', (code) => {
      const root = stdout.trim()
      resolvePromise(code === 0 && root.length > 0 ? root : undefined)
    })
    child.on('error', () => resolvePromise(undefined))
  })
}
