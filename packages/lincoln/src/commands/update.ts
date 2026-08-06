import { spawn } from 'node:child_process'
import type { LincolnPaths } from '../lib/paths.js'
import { resolveLincolnPaths } from '../lib/paths.js'
import { readVersionMarker } from '../lib/versionMarker.js'
import { createRegistryClient } from '../lib/npmRegistry.js'
import { compareVersions } from '../lib/semver.js'
import { readLocalPackageVersion } from '../lib/packageInfo.js'
import { install } from './install.js'
import type { InstallOptions } from './install.js'

const PACKAGE_NAME = '@sushanglewis/lincoln'

export interface UpdateOptions {
  check: boolean
  dryRun: boolean
  yes: boolean
}

export interface UpdateDeps {
  paths: LincolnPaths
  latestVersion: () => Promise<string>
  currentVersion: () => string | undefined
  npmInstallGlobal: (version: string) => Promise<number>
  runInstall: (options: InstallOptions) => Promise<number>
}

export function createDefaultDeps(): UpdateDeps {
  const paths = resolveLincolnPaths()
  const registry = createRegistryClient()
  return {
    paths,
    latestVersion: () => registry.latestVersion(PACKAGE_NAME),
    currentVersion: () => readVersionMarker(paths)?.version ?? readLocalPackageVersion(),
    npmInstallGlobal: (version) => runNpmInstallGlobal(PACKAGE_NAME, version),
    runInstall: (options) => install(options)
  }
}

export async function update(
  options: UpdateOptions,
  deps: Partial<UpdateDeps> = {}
): Promise<number> {
  const resolved: UpdateDeps = { ...createDefaultDeps(), ...deps }

  let latest: string
  try {
    latest = await resolved.latestVersion()
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    console.error(`Failed to query npm registry: ${message}`)
    return 1
  }

  const current = resolved.currentVersion()

  if (current !== undefined) {
    const comparison = compareVersions(current, latest)
    if (comparison !== undefined ? comparison > 0 : false) {
      console.log(
        `Lincoln ${current} is ahead of the latest release (${latest}); nothing to do.`
      )
      return 0
    }
    if (comparison !== undefined ? comparison === 0 : current === latest) {
      console.log(`Lincoln ${current} is already up to date.`)
      return 0
    }
  }

  const summary = `${current ?? 'unknown'} -> ${latest}`

  if (options.check) {
    console.log(`Lincoln update available: ${summary}`)
    return 0
  }

  if (options.dryRun) {
    console.log(`Dry run: would update Lincoln ${summary}`)
    return 0
  }

  if (!options.yes) {
    console.error(`Will update Lincoln ${summary}. Run with --yes to proceed.`)
    return 1
  }

  const installCode = await resolved.npmInstallGlobal(latest)
  if (installCode !== 0) {
    console.error(`npm install -g ${PACKAGE_NAME}@${latest} failed with exit code ${installCode}`)
    return 1
  }

  // NOTE: this runs the *current* process's install(), not the just-installed
  // new version's. Re-executing the freshly installed `lincoln` binary would
  // rely on PATH/npx resolution picking up the new shim, which is fragile
  // mid-upgrade. The tradeoff is that sync logic changes shipped in the new
  // version only take effect on the next command run.
  const syncCode = await resolved.runInstall(defaultInstallOptions())
  if (syncCode !== 0) {
    console.error(`lincoln install failed with exit code ${syncCode}`)
    return 1
  }

  console.log(`Updated Lincoln to ${latest}`)
  return 0
}

function defaultInstallOptions(): InstallOptions {
  return { yes: true, dryRun: false, force: false, harnesses: [], noVenv: true, noInteractive: true }
}

function runNpmInstallGlobal(packageName: string, version: string): Promise<number> {
  return new Promise((resolvePromise) => {
    const child = spawn('npm', ['install', '-g', `${packageName}@${version}`], {
      stdio: 'inherit',
      shell: process.platform === 'win32',
      env: { ...process.env, LINCOLN_SKIP_POSTINSTALL: '1' }
    })
    child.on('close', (code) => resolvePromise(code ?? 1))
    child.on('error', () => resolvePromise(1))
  })
}
