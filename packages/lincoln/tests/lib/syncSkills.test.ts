import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { syncExternalSkills } from '../../src/lib/syncSkills.js'
import type { CommandRunner, SyncExternalSkillsOptions } from '../../src/lib/syncSkills.js'

interface RecordedCall {
  cmd: string
  args: string[]
}

function makeRunner(handler?: (call: RecordedCall) => { code: number; stdout: string; stderr: string }) {
  const calls: RecordedCall[] = []
  const runCommand: CommandRunner = async (cmd, args) => {
    const call = { cmd, args }
    calls.push(call)
    return handler ? handler(call) : { code: 0, stdout: '', stderr: '' }
  }
  return { calls, runCommand }
}

const SUPER_SHA = '8ca22dba9a94f28898bbce59f2537ff4d87c747d'
const OMC_SHA = '454bae017356ed1d056182cd929b6eb6cf6143ad'

function manifestYaml(): string {
  return `skills:
  superpowers:
    source: https://github.com/obra/superpowers.git
    ref: ${SUPER_SHA}
    pinned_from: main
    type: skill
    required: true
  gsd:
    source: https://github.com/gsd-build/get-shit-done.git
    ref: bdcaab2c752d9a33a1a1ca9acf3a3c81fb991815
    type: skill
    required: true
  oh-my-claudecode:
    source: https://github.com/Yeachan-Heo/oh-my-claudecode.git
    ref: ${OMC_SHA}
    type: plugin
    required: false
    default_install: true
  lc-status:
    source: inline
    type: skill
    path: .claude/skills/lc-status
  openspec:
    source: https://github.com/Fission-AI/openspec.git
    ref: v1.14.1
    type: cli
    binary: openspec
    required: true
    platforms:
      macos: npm install -g @fission-ai/openspec
      linux: npm install -g @fission-ai/openspec
`
}

describe('syncExternalSkills', () => {
  let tmpDir: string
  let payloadRoot: string
  let skillsDir: string

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lincoln-synckills-test-'))
    payloadRoot = path.join(tmpDir, 'payload')
    skillsDir = path.join(tmpDir, '.claude', 'skills')
    fs.mkdirSync(path.join(payloadRoot, '.claude', 'skills'), { recursive: true })
    fs.writeFileSync(path.join(payloadRoot, '.claude', 'skills', 'dependencies.yaml'), manifestYaml())
  })

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true })
  })

  function makeOpts(runCommand: CommandRunner): SyncExternalSkillsOptions {
    return { payloadRoot, skillsDir, dryRun: false, runCommand }
  }

  it('warns and returns empty report when manifest is missing', async () => {
    fs.rmSync(path.join(payloadRoot, '.claude', 'skills', 'dependencies.yaml'))
    const { calls, runCommand } = makeRunner()

    const report = await syncExternalSkills(makeOpts(runCommand))

    expect(calls).toHaveLength(0)
    expect(report.entries).toHaveLength(0)
    expect(report.warnings.some((w) => w.includes('dependencies.yaml'))).toBe(true)
  })

  it('clones and checks out a missing skill', async () => {
    const { calls, runCommand } = makeRunner()

    const report = await syncExternalSkills(makeOpts(runCommand))

    const superpowers = report.entries.find((e) => e.name === 'superpowers')
    expect(superpowers?.status).toBe('installed')
    expect(calls).toContainEqual({
      cmd: 'git',
      args: ['clone', 'https://github.com/obra/superpowers.git', path.join(skillsDir, 'superpowers')]
    })
    expect(calls).toContainEqual({
      cmd: 'git',
      args: ['-C', path.join(skillsDir, 'superpowers'), 'checkout', SUPER_SHA]
    })
  })

  it('reports current when local HEAD equals the pin without network calls', async () => {
    fs.mkdirSync(path.join(skillsDir, 'superpowers'), { recursive: true })
    const { calls, runCommand } = makeRunner((call) => {
      if (call.args[2] === 'status') return { code: 0, stdout: '', stderr: '' }
      if (call.args[2] === 'rev-parse') return { code: 0, stdout: `${SUPER_SHA}\n`, stderr: '' }
      return { code: 1, stdout: '', stderr: 'unexpected' }
    })

    const report = await syncExternalSkills(makeOpts(runCommand))

    const superpowers = report.entries.find((e) => e.name === 'superpowers')
    expect(superpowers?.status).toBe('current')
    expect(calls.some((c) => c.args[1] === 'fetch')).toBe(false)
    expect(calls.some((c) => c.args[1] === 'ls-remote')).toBe(false)
  })

  it('fetches and checks out FETCH_HEAD when local HEAD is behind the pin', async () => {
    fs.mkdirSync(path.join(skillsDir, 'superpowers'), { recursive: true })
    const { calls, runCommand } = makeRunner((call) => {
      if (call.args[2] === 'status') return { code: 0, stdout: '', stderr: '' }
      if (call.args[2] === 'rev-parse') return { code: 0, stdout: '6fd4507659784c351abbd2bc264c7162cfd386dc\n', stderr: '' }
      if (call.args[0] === 'ls-remote') return { code: 0, stdout: `${SUPER_SHA}\trefs/heads/main\n`, stderr: '' }
      return { code: 0, stdout: '', stderr: '' }
    })

    const report = await syncExternalSkills(makeOpts(runCommand))

    const superpowers = report.entries.find((e) => e.name === 'superpowers')
    expect(superpowers?.status).toBe('updated')
    expect(calls).toContainEqual({
      cmd: 'git',
      args: ['-C', path.join(skillsDir, 'superpowers'), 'fetch', 'origin', SUPER_SHA]
    })
    expect(calls).toContainEqual({
      cmd: 'git',
      args: ['-C', path.join(skillsDir, 'superpowers'), 'checkout', 'FETCH_HEAD']
    })
  })

  it('skips dirty working trees with a warning', async () => {
    fs.mkdirSync(path.join(skillsDir, 'superpowers'), { recursive: true })
    const { calls, runCommand } = makeRunner((call) => {
      if (call.args[2] === 'status') return { code: 0, stdout: ' M SKILL.md\n', stderr: '' }
      return { code: 0, stdout: '', stderr: '' }
    })

    const report = await syncExternalSkills(makeOpts(runCommand))

    const superpowers = report.entries.find((e) => e.name === 'superpowers')
    expect(superpowers?.status).toBe('skipped-dirty')
    expect(report.warnings.some((w) => w.includes('superpowers') && w.includes('dirty'))).toBe(true)
    expect(calls.some((c) => c.args[1] === 'fetch')).toBe(false)
  })

  it('skips optional plugins when default_install is false', async () => {
    const depFile = path.join(payloadRoot, '.claude', 'skills', 'dependencies.yaml')
    fs.writeFileSync(depFile, manifestYaml().replace('    default_install: true\n', '    default_install: false\n'))
    const { calls, runCommand } = makeRunner()

    const report = await syncExternalSkills(makeOpts(runCommand))

    const omc = report.entries.find((e) => e.name === 'oh-my-claudecode')
    expect(omc?.status).toBe('skipped-optional')
    expect(calls.some((c) => c.args.join(' ').includes('oh-my-claudecode'))).toBe(false)
  })

  it('never touches inline skills', async () => {
    const { calls, runCommand } = makeRunner()

    const report = await syncExternalSkills(makeOpts(runCommand))

    expect(report.entries.find((e) => e.name === 'lc-status')).toBeUndefined()
    expect(calls.some((c) => c.args.join(' ').includes('lc-status'))).toBe(false)
  })

  it('executes no commands in dry-run mode but reports planned actions', async () => {
    const { calls, runCommand } = makeRunner()

    const report = await syncExternalSkills({ ...makeOpts(runCommand), dryRun: true })

    expect(calls).toHaveLength(0)
    expect(report.entries.find((e) => e.name === 'superpowers')?.status).toBe('dry-run')
    expect(report.entries.find((e) => e.name === 'oh-my-claudecode')?.status).toBe('dry-run')
  })

  it('reports failed when clone fails', async () => {
    const { calls, runCommand } = makeRunner((call) => {
      if (call.args[0] === 'clone') return { code: 128, stdout: '', stderr: 'network unreachable' }
      return { code: 0, stdout: '', stderr: '' }
    })

    const report = await syncExternalSkills(makeOpts(runCommand))

    const superpowers = report.entries.find((e) => e.name === 'superpowers')
    expect(superpowers?.status).toBe('failed')
    expect(superpowers?.detail).toContain('network unreachable')
    expect(report.warnings.some((w) => w.includes('superpowers'))).toBe(true)
  })

  it('falls back to full fetch + checkout by SHA when ls-remote cannot resolve the pin', async () => {
    fs.mkdirSync(path.join(skillsDir, 'superpowers'), { recursive: true })
    const { calls, runCommand } = makeRunner((call) => {
      if (call.args[2] === 'status') return { code: 0, stdout: '', stderr: '' }
      if (call.args[2] === 'rev-parse') return { code: 0, stdout: '6fd4507659784c351abbd2bc264c7162cfd386dc\n', stderr: '' }
      if (call.args[0] === 'ls-remote') return { code: 0, stdout: '', stderr: '' }
      if (call.args[2] === 'fetch' && call.args.length === 5) return { code: 128, stdout: '', stderr: 'not found' }
      return { code: 0, stdout: '', stderr: '' }
    })

    const report = await syncExternalSkills(makeOpts(runCommand))

    expect(report.entries.find((e) => e.name === 'superpowers')?.status).toBe('updated')
    expect(calls).toContainEqual({
      cmd: 'git',
      args: ['-C', path.join(skillsDir, 'superpowers'), 'fetch', 'origin']
    })
    expect(calls).toContainEqual({
      cmd: 'git',
      args: ['-C', path.join(skillsDir, 'superpowers'), 'checkout', SUPER_SHA]
    })
  })

  it('marks a present CLI as current without running installs', async () => {
    const { calls, runCommand } = makeRunner((call) => {
      if (call.cmd === 'which') return { code: 0, stdout: '/usr/local/bin/openspec\n', stderr: '' }
      return { code: 0, stdout: '', stderr: '' }
    })

    const report = await syncExternalSkills(makeOpts(runCommand))

    expect(report.entries.find((e) => e.name === 'openspec')?.status).toBe('current')
    expect(calls.some((c) => c.cmd === 'npm')).toBe(false)
  })

  it('installs a missing npm-managed CLI at the pinned version', async () => {
    const { calls, runCommand } = makeRunner((call) => {
      if (call.cmd === 'which') return { code: 1, stdout: '', stderr: '' }
      return { code: 0, stdout: '', stderr: '' }
    })

    const report = await syncExternalSkills(makeOpts(runCommand))

    expect(report.entries.find((e) => e.name === 'openspec')?.status).toBe('installed')
    expect(calls).toContainEqual({
      cmd: 'npm',
      args: ['install', '-g', '@fission-ai/openspec@1.14.1']
    })
  })

  it('upgrades an npm-managed CLI when its version is older than the pin', async () => {
    const { calls, runCommand } = makeRunner((call) => {
      if (call.cmd === 'which') return { code: 0, stdout: '/usr/local/bin/openspec\n', stderr: '' }
      if (call.args[0] === '--version') return { code: 0, stdout: '0.5.0\n', stderr: '' }
      return { code: 0, stdout: '', stderr: '' }
    })

    const report = await syncExternalSkills(makeOpts(runCommand))

    expect(report.entries.find((e) => e.name === 'openspec')?.status).toBe('updated')
    expect(calls).toContainEqual({
      cmd: 'npm',
      args: ['install', '-g', '@fission-ai/openspec@1.14.1']
    })
  })

  it('warns without auto-installing when a non-npm CLI is missing', async () => {
    const depFile = path.join(payloadRoot, '.claude', 'skills', 'dependencies.yaml')
    fs.writeFileSync(
      depFile,
      `${manifestYaml()}  gh:
    source: https://cli.github.com/
    type: cli
    binary: gh
    required: true
    platforms:
      macos: brew install gh
      linux: sudo apt-get install gh
`
    )
    const { calls, runCommand } = makeRunner((call) => {
      if (call.cmd === 'which') return { code: 1, stdout: '', stderr: '' }
      return { code: 0, stdout: '', stderr: '' }
    })

    const report = await syncExternalSkills(makeOpts(runCommand))

    expect(report.entries.find((e) => e.name === 'gh')?.status).toBe('failed')
    expect(report.warnings.some((w) => w.includes('gh') && w.includes('brew install gh'))).toBe(true)
    expect(calls.some((c) => c.cmd === 'brew')).toBe(false)
  })
})
