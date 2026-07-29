import React, { useEffect } from 'react'
import { Text } from 'ink'
import { describe, expect, test, vi, afterEach } from 'vitest'
import { render } from 'ink-testing-library'
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { useSetup, type StepResult } from '../../src/hooks/useSetup'
import * as runSetupModule from '../../src/utils/runSetup'

afterEach(() => {
  vi.restoreAllMocks()
})

function createProjectDir(): string {
  const root = mkdtempSync(join(tmpdir(), 'lincoln-'))
  const scriptsDir = join(root, 'scripts')
  mkdirSync(scriptsDir)
  writeFileSync(join(scriptsDir, 'lincoln-setup.py'), '')
  return root
}

describe('useSetup', () => {
  const dirs: string[] = []

  afterEach(() => {
    for (const dir of dirs) {
      rmSync(dir, { recursive: true, force: true })
    }
    dirs.length = 0
  })

  test('initial state is idle with no results', () => {
    function C() {
      const { isRunning, results } = useSetup()
      return (
        <Text>
          {isRunning ? 'running' : 'idle'}:{results.length}
        </Text>
      )
    }
    const { lastFrame } = render(<C />)
    expect(lastFrame()).toBe('idle:0')
  })

  test('startSetup runs all steps and completes on success', async () => {
    vi.spyOn(runSetupModule, 'runSetup').mockResolvedValue({
      success: true,
      code: 0,
      stdout: '{"ok":true}',
      stderr: '',
    })

    const root = createProjectDir()
    dirs.push(root)
    let complete = false
    let latestResults: StepResult[] = []

    function TestHarness() {
      const { isRunning, results, startSetup } = useSetup()

      useEffect(() => {
        startSetup({
          root,
          harnesses: ['claude-code'],
          yes: true,
          dryRun: false,
        })
      }, [])

      useEffect(() => {
        if (!isRunning && results.length > 0) {
          complete = true
        }
      }, [isRunning, results])

      latestResults = results
      return <Text>{isRunning ? 'running' : 'idle'}</Text>
    }

    render(<TestHarness />)

    await vi.waitFor(() => expect(complete).toBe(true), {
      timeout: 2000,
    })
    expect(latestResults.every((r) => r.success)).toBe(true)
  })

  test('startSetup records failure when a step fails', async () => {
    vi.spyOn(runSetupModule, 'runSetup').mockResolvedValue({
      success: false,
      code: 1,
      stdout: '',
      stderr: 'missing dependency',
    })

    const root = createProjectDir()
    dirs.push(root)
    let complete = false
    let latestResults: StepResult[] = []

    function TestHarness() {
      const { isRunning, results, startSetup } = useSetup()

      useEffect(() => {
        startSetup({
          root,
          harnesses: [],
          yes: true,
          dryRun: false,
        })
      }, [])

      useEffect(() => {
        if (!isRunning && results.length > 0) {
          complete = true
        }
      }, [isRunning, results])

      latestResults = results
      return <Text>{isRunning ? 'running' : 'idle'}</Text>
    }

    render(<TestHarness />)

    await vi.waitFor(() => expect(complete).toBe(true), {
      timeout: 2000,
    })
    expect(latestResults[0].success).toBe(false)
  })

  test('records error when startSetup throws', async () => {
    vi.spyOn(runSetupModule, 'runSetup').mockRejectedValue(new Error('spawn failed'))

    const root = createProjectDir()
    dirs.push(root)
    let capturedError: string | undefined

    function TestHarness() {
      const { isRunning, error, startSetup } = useSetup()

      useEffect(() => {
        startSetup({
          root,
          harnesses: [],
          yes: true,
          dryRun: false,
        })
      }, [])

      useEffect(() => {
        if (!isRunning && error) {
          capturedError = error
        }
      }, [isRunning, error])

      return <Text>{isRunning ? 'running' : 'idle'}</Text>
    }

    render(<TestHarness />)

    await vi.waitFor(() => expect(capturedError).toBeTruthy(), {
      timeout: 2000,
    })
    expect(capturedError).toContain('spawn failed')
  })

  test('stops after install-skills fails', async () => {
    let callCount = 0
    vi.spyOn(runSetupModule, 'runSetup').mockImplementation(async () => {
      callCount++
      if (callCount === 1) {
        return { success: true, code: 0, stdout: '{"ok":true}', stderr: '' }
      }
      return { success: false, code: 1, stdout: '', stderr: 'missing skill' }
    })

    const root = createProjectDir()
    dirs.push(root)
    let complete = false
    let latestResults: StepResult[] = []

    function TestHarness() {
      const { isRunning, results, startSetup } = useSetup()

      useEffect(() => {
        startSetup({
          root,
          harnesses: [],
          yes: true,
          dryRun: false,
        })
      }, [])

      useEffect(() => {
        if (!isRunning && results.length > 1) {
          complete = true
        }
      }, [isRunning, results])

      latestResults = results
      return <Text>{isRunning ? 'running' : 'idle'}</Text>
    }

    render(<TestHarness />)

    await vi.waitFor(() => expect(complete).toBe(true), {
      timeout: 2000,
    })
    expect(latestResults[0].success).toBe(true)
    expect(latestResults[1].success).toBe(false)
  })
})
