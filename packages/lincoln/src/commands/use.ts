import fs from 'node:fs'
import path from 'node:path'
import { spawn } from 'node:child_process'
import type { LincolnPaths } from '../lib/paths.js'
import { resolveLincolnPaths } from '../lib/paths.js'
import { install } from './install.js'
import type { InstallOptions } from './install.js'

const PACKAGE_NAME = '@sushanglewis/lincoln'
const SEMVER_REGEX = /^v?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/
const DIST_TAG_REGEX = /^[a-zA-Z][a-zA-Z0-9._-]*$/

export interface UseOptions {
  dryRun: boolean
  yes: boolean
}

export interface UseDeps {
  paths: LincolnPaths
  ensureVersionAvailable: (version: string) => Promise<void>
  runInstall: (options: InstallOptions) => Promise<number>
}

export function createDefaultDeps(): UseDeps {
  const paths = resolveLincolnPaths()
  return {
    paths,
    ensureVersionAvailable: async (version) => {
      const code = await runNpmInstallGlobal(PACKAGE_NAME, version)
      if (code !== 0) {
        throw new Error(`npm install -g ${PACKAGE_NAME}@${version} exited with ${code}`)
      }
    },
    runInstall: (options) => install(options)
  }
}

export async function use(
  version: string,
  options: UseOptions,
  deps: Partial<UseDeps> = {}
): Promise<number> {
  if (!isValidVersion(version)) {
    console.error(`Invalid version: ${version}`)
    return 1
  }

  const resolved: UseDeps = { ...createDefaultDeps(), ...deps }
  const versionDir = path.join(resolved.paths.versionsDir, version)
  const alreadyInstalled = fs.existsSync(versionDir)

  if (options.dryRun) {
    if (alreadyInstalled) {
      console.log(`Dry run: would switch ~/.lincoln/current to versions/${version}`)
    } else {
      console.log(`Dry run: would install ${PACKAGE_NAME}@${version} globally, then switch`)
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
  }

  if (fs.existsSync(versionDir)) {
    try {
      switchCurrentLink(resolved.paths, versionDir)
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      console.error(`Failed to switch ~/.lincoln/current: ${message}`)
      return 1
    }
  }

  const syncCode = await resolved.runInstall(defaultInstallOptions())
  if (syncCode !== 0) {
    console.error(`lincoln install failed with exit code ${syncCode}`)
    return 1
  }

  console.log(`Switched Lincoln to ${version}`)
  return 0
}

function isValidVersion(version: string): boolean {
  return SEMVER_REGEX.test(version) || DIST_TAG_REGEX.test(version)
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
