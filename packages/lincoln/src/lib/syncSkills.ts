import fs from 'node:fs'
import path from 'node:path'
import { execFile } from 'node:child_process'
import yaml from 'js-yaml'
import { compareVersions } from './semver.js'

export type CommandRunner = (
  cmd: string,
  args: string[]
) => Promise<{ code: number; stdout: string; stderr: string }>

export type SkillSyncStatus =
  | 'installed'
  | 'updated'
  | 'current'
  | 'failed'
  | 'skipped-optional'
  | 'skipped-dirty'
  | 'dry-run'

export interface SkillSyncEntry {
  name: string
  status: SkillSyncStatus
  detail?: string
}

export interface SkillSyncReport {
  entries: SkillSyncEntry[]
  warnings: string[]
}

export interface SyncExternalSkillsOptions {
  payloadRoot: string
  skillsDir: string
  dryRun: boolean
  runCommand?: CommandRunner
}

interface ManifestEntry {
  source?: string
  ref?: string
  type?: string
  required?: boolean
  default_install?: boolean
  binary?: string
  platforms?: Record<string, string>
}

interface SkillManifest {
  skills?: Record<string, ManifestEntry>
}

const GIT_SOURCE = /^(https?:\/\/|git@)/
const FULL_SHA = /^[0-9a-f]{40}$/i
const PINNED_SEMVER = /^v?(\d+\.\d+\.\d+)$/
const NPM_GLOBAL_INSTALL = /^npm install -g (\S+)$/
const MAX_BUFFER = 16 * 1024 * 1024

const defaultRunner: CommandRunner = (cmd, args) =>
  new Promise((resolvePromise, rejectPromise) => {
    execFile(cmd, args, { maxBuffer: MAX_BUFFER }, (err, stdout, stderr) => {
      if (err && !('code' in err && typeof err.code === 'number')) {
        rejectPromise(err)
        return
      }
      const code = err && typeof err.code === 'number' ? err.code : 0
      resolvePromise({ code, stdout: String(stdout), stderr: String(stderr) })
    })
  })

export async function syncExternalSkills(options: SyncExternalSkillsOptions): Promise<SkillSyncReport> {
  const report: SkillSyncReport = { entries: [], warnings: [] }
  const manifestPath = path.join(options.payloadRoot, '.claude', 'skills', 'dependencies.yaml')
  if (!fs.existsSync(manifestPath)) {
    report.warnings.push(`skill dependency manifest not found at ${manifestPath}; skipping external skill sync`)
    return report
  }

  let manifest: SkillManifest
  try {
    manifest = (yaml.load(fs.readFileSync(manifestPath, 'utf8')) as SkillManifest) ?? {}
  } catch (err) {
    report.warnings.push(
      `failed to parse ${manifestPath}: ${err instanceof Error ? err.message : String(err)}`
    )
    return report
  }

  const runCommand = options.runCommand ?? defaultRunner
  for (const [name, cfg] of Object.entries(manifest.skills ?? {})) {
    if (!cfg.source || cfg.source === 'inline' || !GIT_SOURCE.test(cfg.source)) {
      continue
    }
    const enabled = cfg.default_install ?? cfg.required ?? true
    if (!enabled) {
      report.entries.push({ name, status: 'skipped-optional', detail: 'default_install is false' })
      continue
    }
    if (cfg.type === 'cli') {
      await syncCli(name, cfg, options, runCommand, report)
    } else {
      await syncGitSkill(name, cfg, options, runCommand, report)
    }
  }
  return report
}

async function syncGitSkill(
  name: string,
  cfg: ManifestEntry,
  options: SyncExternalSkillsOptions,
  runCommand: CommandRunner,
  report: SkillSyncReport
): Promise<void> {
  const source = cfg.source as string
  const ref = cfg.ref ?? ''
  const target = path.join(options.skillsDir, name)

  if (options.dryRun) {
    const planned = fs.existsSync(target) ? 'verify pinned ref and update if behind' : `clone and pin to ${ref}`
    report.entries.push({ name, status: 'dry-run', detail: `would ${planned}` })
    return
  }

  if (!fs.existsSync(target)) {
    const clone = await runCommand('git', ['clone', source, target])
    if (clone.code !== 0) {
      fail(report, name, `git clone failed: ${clone.stderr.trim() || `exit code ${clone.code}`}`)
      return
    }
    const checkout = await runCommand('git', ['-C', target, 'checkout', ref])
    if (checkout.code !== 0) {
      fail(report, name, `git checkout ${ref} failed: ${checkout.stderr.trim() || `exit code ${checkout.code}`}`)
      return
    }
    report.entries.push({ name, status: 'installed', detail: ref })
    return
  }

  const status = await runCommand('git', ['-C', target, 'status', '--porcelain'])
  if (status.code !== 0) {
    fail(report, name, `git status failed (not a git repository?): ${status.stderr.trim() || `exit code ${status.code}`}`)
    return
  }
  if (status.stdout.trim() !== '') {
    const detail = 'working tree is dirty; skipping update (commit or stash local changes first)'
    report.entries.push({ name, status: 'skipped-dirty', detail })
    report.warnings.push(`${name}: ${detail}`)
    return
  }

  const head = await runCommand('git', ['-C', target, 'rev-parse', 'HEAD'])
  if (head.code !== 0) {
    fail(report, name, `git rev-parse failed: ${head.stderr.trim() || `exit code ${head.code}`}`)
    return
  }
  if (head.stdout.trim() === ref) {
    report.entries.push({ name, status: 'current', detail: ref })
    return
  }

  const advertised = await isPinAdvertised(source, ref, runCommand)
  if (advertised) {
    const fetch = await runCommand('git', ['-C', target, 'fetch', 'origin', ref])
    if (fetch.code === 0 && (await checkoutFetchHead(name, target, runCommand, report))) {
      return
    }
    if (fetch.code !== 0) {
      fail(report, name, `git fetch origin ${ref} failed: ${fetch.stderr.trim() || `exit code ${fetch.code}`}`)
      return
    }
    return
  }

  const fetch = await runCommand('git', ['-C', target, 'fetch', 'origin', ref])
  if (fetch.code === 0) {
    await checkoutFetchHead(name, target, runCommand, report)
    return
  }
  if (FULL_SHA.test(ref)) {
    const fetchAll = await runCommand('git', ['-C', target, 'fetch', 'origin'])
    if (fetchAll.code !== 0) {
      fail(report, name, `git fetch origin failed: ${fetchAll.stderr.trim() || `exit code ${fetchAll.code}`}`)
      return
    }
    const checkout = await runCommand('git', ['-C', target, 'checkout', ref])
    if (checkout.code !== 0) {
      fail(report, name, `git checkout ${ref} failed: ${checkout.stderr.trim() || `exit code ${checkout.code}`}`)
      return
    }
    report.entries.push({ name, status: 'updated', detail: ref })
    return
  }
  fail(report, name, `git fetch origin ${ref} failed: ${fetch.stderr.trim() || `exit code ${fetch.code}`}`)
}

async function isPinAdvertised(
  source: string,
  ref: string,
  runCommand: CommandRunner
): Promise<boolean> {
  const remote = await runCommand('git', ['ls-remote', source])
  if (remote.code !== 0) {
    return false
  }
  return remote.stdout
    .split('\n')
    .some((line) => line.split('\t')[0]?.trim() === ref)
}

async function checkoutFetchHead(
  name: string,
  target: string,
  runCommand: CommandRunner,
  report: SkillSyncReport
): Promise<boolean> {
  const checkout = await runCommand('git', ['-C', target, 'checkout', 'FETCH_HEAD'])
  if (checkout.code !== 0) {
    fail(report, name, `git checkout FETCH_HEAD failed: ${checkout.stderr.trim() || `exit code ${checkout.code}`}`)
    return false
  }
  report.entries.push({ name, status: 'updated', detail: 'checked out FETCH_HEAD' })
  return true
}

async function syncCli(
  name: string,
  cfg: ManifestEntry,
  options: SyncExternalSkillsOptions,
  runCommand: CommandRunner,
  report: SkillSyncReport
): Promise<void> {
  const binary = cfg.binary ?? name
  const platform = process.platform === 'darwin' ? 'macos' : process.platform === 'linux' ? 'linux' : process.platform
  const installCommand = cfg.platforms?.[platform] ?? cfg.platforms?.linux
  const npmPackage = installCommand ? parseNpmGlobalInstall(installCommand) : undefined
  const pinned = cfg.ref ? pinnedSemver(cfg.ref) : undefined

  if (options.dryRun) {
    const managed = npmPackage && pinned ? `install ${npmPackage}@${pinned} if missing or older` : 'verify presence'
    report.entries.push({ name, status: 'dry-run', detail: `would ${managed}` })
    return
  }

  const whichCmd = process.platform === 'win32' ? 'where' : 'which'
  const found = await runCommand(whichCmd, [binary])
  if (found.code !== 0) {
    if (npmPackage && pinned) {
      await npmInstall(name, npmPackage, pinned, runCommand, report, 'installed')
      return
    }
    fail(report, name, `CLI '${binary}' not found. Install manually (${platform}): ${installCommand ?? 'see dependency manifest'}`)
    return
  }

  if (!npmPackage || !pinned) {
    report.entries.push({ name, status: 'current', detail: `${binary} present` })
    return
  }

  const version = await runCommand(binary, ['--version'])
  const installed = version.code === 0 ? version.stdout.split('\n')[0]?.trim() ?? '' : ''
  const comparison = installed ? compareVersions(installed, pinned) : undefined
  if (comparison === undefined) {
    report.entries.push({
      name,
      status: 'current',
      detail: `could not parse installed version '${installed}'; leaving ${binary} as-is`
    })
    return
  }
  if (comparison >= 0) {
    report.entries.push({ name, status: 'current', detail: `${binary} ${installed}` })
    return
  }
  await npmInstall(name, npmPackage, pinned, runCommand, report, 'updated')
}

async function npmInstall(
  name: string,
  npmPackage: string,
  version: string,
  runCommand: CommandRunner,
  report: SkillSyncReport,
  status: 'installed' | 'updated'
): Promise<void> {
  const result = await runCommand('npm', ['install', '-g', `${npmPackage}@${version}`])
  if (result.code !== 0) {
    fail(report, name, `npm install -g ${npmPackage}@${version} failed: ${result.stderr.trim() || `exit code ${result.code}`}`)
    return
  }
  report.entries.push({ name, status, detail: `${npmPackage}@${version}` })
}

function parseNpmGlobalInstall(command: string): string | undefined {
  const match = NPM_GLOBAL_INSTALL.exec(command.trim())
  return match?.[1]
}

function pinnedSemver(ref: string): string | undefined {
  const match = PINNED_SEMVER.exec(ref.trim())
  return match?.[0].replace(/^v/, '')
}

function fail(report: SkillSyncReport, name: string, detail: string): void {
  report.entries.push({ name, status: 'failed', detail })
  report.warnings.push(`${name}: ${detail}`)
}
