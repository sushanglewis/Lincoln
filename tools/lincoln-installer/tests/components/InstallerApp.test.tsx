import React from 'react'
import { describe, expect, test, vi, beforeEach, afterEach } from 'vitest'
import { render } from 'ink-testing-library'
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { InstallerApp } from '../../src/components/InstallerApp'
import type { InstallerConfig } from '../../src/config/resolveConfig'
import * as runSetupModule from '../../src/utils/runSetup'

async function tick() {
  return new Promise((resolve) => setTimeout(resolve, 0))
}

function createProjectDir(): string {
  const root = mkdtempSync(join(tmpdir(), 'lincoln-'))
  const scriptsDir = join(root, 'scripts')
  mkdirSync(scriptsDir)
  writeFileSync(join(scriptsDir, 'lincoln-setup.py'), '')
  return root
}

describe('InstallerApp', () => {
  const dirs: string[] = []

  beforeEach(() => {
    vi.spyOn(runSetupModule, 'runSetup').mockResolvedValue({
      success: true,
      code: 0,
      stdout: '{"ok":true}',
      stderr: '',
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
    for (const dir of dirs) {
      rmSync(dir, { recursive: true, force: true })
    }
    dirs.length = 0
  })

  test('renders welcome screen by default', () => {
    const root = createProjectDir()
    dirs.push(root)
    const config: InstallerConfig = {
      root,
      harnesses: [],
      yes: false,
      dryRun: false,
      format: 'human',
    }
    const { lastFrame } = render(<InstallerApp config={config} />)
    expect(lastFrame() ?? '').toContain('Welcome to Lincoln')
  })

  test('navigates from welcome to summary via input', async () => {
    const root = createProjectDir()
    dirs.push(root)
    const config: InstallerConfig = {
      root,
      harnesses: [],
      yes: false,
      dryRun: false,
      format: 'human',
    }
    const { lastFrame, stdin } = render(<InstallerApp config={config} />)

    await tick()
    stdin.write('\r')
    await tick()
    expect(lastFrame() ?? '').toContain('Select agent harnesses')

    stdin.write('\r')
    await tick()
    expect(lastFrame() ?? '').toContain('Options')

    stdin.write('\r')
    await tick()
    expect(lastFrame() ?? '').toContain('Summary')

    stdin.write('\r')
    await tick()
    await vi.waitFor(() => expect(lastFrame() ?? '').toContain('complete'), {
      timeout: 2000,
    })
  })
})
