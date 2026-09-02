import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { doctor } from '../../src/commands/doctor.js'
import { resolveLincolnPaths } from '../../src/lib/paths.js'
import { writeVersionMarker } from '../../src/lib/versionMarker.js'

describe('doctor', () => {
  let tmpDir: string

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lincoln-doctor-test-'))
  })

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true })
  })

  function makeDeps(overrides: Record<string, unknown> = {}) {
    const paths = resolveLincolnPaths(tmpDir)
    return {
      paths,
      nodeVersion: () => process.version,
      pythonVersion: async () => '3.11.0',
      pyyamlVersion: async () => '6.0.1',
      npmVersion: async () => '10.2.0',
      projectRoot: tmpDir,
      ...overrides
    }
  }

  it('reports missing marker as warning', async () => {
    const result = await doctor({ json: true }, makeDeps({ projectRoot: '/tmp/empty' }))
    expect(result.code).toBe(0)
    const markerCheck = result.checks.find((c) => c.name === 'project-marker')
    expect(markerCheck).toEqual(expect.objectContaining({ name: 'project-marker', status: 'skip' }))
  })

  it('reports ok for all healthy checks', async () => {
    const paths = resolveLincolnPaths(tmpDir)
    fs.mkdirSync(paths.currentDir, { recursive: true })
    fs.mkdirSync(path.join(paths.currentDir, '.claude', 'hooks'), { recursive: true })
    fs.writeFileSync(path.join(paths.currentDir, '.claude', 'hooks', 'on-session-start.sh'), '#')
    fs.mkdirSync(paths.venvDir, { recursive: true })
    const venvBin = path.join(paths.venvDir, 'bin')
    fs.mkdirSync(venvBin, { recursive: true })
    const pythonExe = path.join(venvBin, 'python')
    fs.writeFileSync(pythonExe, '#!/bin/sh\necho ok')
    fs.chmodSync(pythonExe, 0o755)
    writeVersionMarker(paths, {
      version: '1.6.0',
      installedAt: new Date().toISOString(),
      harnesses: ['claude-code'],
      managedFiles: []
    })
    fs.writeFileSync(path.join(tmpDir, '.lincoln.yaml'), 'enabled: true\n')
    fs.mkdirSync(paths.claudeDir, { recursive: true })
    fs.writeFileSync(
      path.join(paths.claudeDir, 'settings.json'),
      JSON.stringify(
        {
          hooks: {
            SessionStart: [
              {
                hooks: [
                  {
                    type: 'command',
                    command: '${CLAUDE_PLUGIN_ROOT}/.claude/hooks/on-session-start.sh',
                    timeout: 60
                  }
                ]
              }
            ],
            PreToolUse: [
              {
                hooks: [
                  {
                    type: 'command',
                    command: '${CLAUDE_PLUGIN_ROOT}/.claude/hooks/pre-tool-use.sh',
                    timeout: 5
                  }
                ]
              }
            ],
            PostToolUse: [
              {
                hooks: [
                  {
                    type: 'command',
                    command: '${CLAUDE_PLUGIN_ROOT}/.claude/hooks/post-tool-use.sh',
                    timeout: 10
                  }
                ]
              }
            ],
            Stop: [
              {
                hooks: [
                  {
                    type: 'command',
                    command: '${CLAUDE_PLUGIN_ROOT}/.claude/hooks/on-stop.sh',
                    timeout: 10
                  }
                ]
              }
            ]
          }
        },
        null,
        2
      )
    )

    const result = await doctor({ json: true }, makeDeps())
    expect(result.code).toBe(0)
    expect(result.checks.every((c) => c.status === 'ok' || c.status === 'skip')).toBe(true)
  })

  it('reports a warning when the global marker is missing', async () => {
    const result = await doctor({ json: true }, makeDeps())
    expect(result.code).toBe(0)
    const markerCheck = result.checks.find((c) => c.name === 'global-marker')
    expect(markerCheck?.status).toBe('warn')
  })

  it('reports an error when node version is below the minimum', async () => {
    const result = await doctor({ json: true }, makeDeps({ nodeVersion: () => 'v18.0.0' }))
    expect(result.code).toBe(1)
    const nodeCheck = result.checks.find((c) => c.name === 'node')
    expect(nodeCheck?.status).toBe('error')
  })

  it('parses prefixed Python version strings', async () => {
    const result = await doctor(
      { json: true },
      makeDeps({ pythonVersion: async () => 'Python 3.11.0' })
    )
    const pythonCheck = result.checks.find((c) => c.name === 'python')
    expect(pythonCheck?.status).toBe('ok')
  })

  it('reports an error when python is unavailable', async () => {
    const result = await doctor(
      { json: true },
      makeDeps({ pythonVersion: async () => undefined })
    )
    expect(result.code).toBe(1)
    const pythonCheck = result.checks.find((c) => c.name === 'python')
    expect(pythonCheck?.status).toBe('error')
  })

  it('reports an error when pyyaml is unavailable', async () => {
    const result = await doctor(
      { json: true },
      makeDeps({ pyyamlVersion: async () => undefined })
    )
    expect(result.code).toBe(1)
    const yamlCheck = result.checks.find((c) => c.name === 'pyyaml')
    expect(yamlCheck?.status).toBe('error')
  })

  it('reports a warning when npm is unavailable', async () => {
    const result = await doctor({ json: true }, makeDeps({ npmVersion: async () => undefined }))
    expect(result.code).toBe(0)
    const npmCheck = result.checks.find((c) => c.name === 'npm')
    expect(npmCheck?.status).toBe('warn')
  })

  it('reports a warning when the payload hooks directory is missing', async () => {
    const result = await doctor({ json: true }, makeDeps())
    const hooksCheck = result.checks.find((c) => c.name === 'payload-hooks')
    expect(hooksCheck?.status).toBe('warn')
  })

  it('reports a warning when the venv is missing', async () => {
    const result = await doctor({ json: true }, makeDeps())
    const venvCheck = result.checks.find((c) => c.name === 'venv')
    expect(venvCheck?.status).toBe('warn')
  })
})
