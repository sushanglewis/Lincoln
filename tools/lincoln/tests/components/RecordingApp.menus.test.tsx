import { render } from 'ink-testing-library'
import React from 'react'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import { RecordingApp } from '../../src/components/RecordingApp'
import type { RecorderController, RecorderState } from '../../src/recording/useRecorder'
import type { ModelStatus } from '../../src/models/models'
import type { WarmupProgress } from '../../src/models/warmupProgress'

const idleState: RecorderState = {
  status: 'idle',
  duration: 0,
  amplitude: 0,
  errorMessage: null,
}

let currentController: RecorderController
const exitMock = vi.fn()

vi.mock('ink', async () => {
  const actual = await vi.importActual<typeof import('ink')>('ink')
  return {
    ...actual,
    useApp: () => ({ exit: exitMock }),
  }
})

vi.mock('../../src/recording/useRecorder', () => ({
  useRecorder: vi.fn(() => currentController),
}))

async function tick(ms = 0) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

const modelStatuses: ModelStatus[] = [
  { name: 'tiny', cached: false },
  { name: 'base', cached: true },
]

function renderApp(extraProps: Record<string, unknown> = {}) {
  return render(
    <RecordingApp
      workspaceRoot="/workspace"
      sessionId="2026-06-28-test"
      topic=""
      designId=""
      branch=""
      audioMeterStyle="bar"
      listDevicesFn={async () => ({
        defaultDevice: 'MacBook Pro Microphone',
        devices: ['MacBook Pro Microphone', 'External Mic'],
      })}
      listModelStatusesFn={async () => modelStatuses}
      runWarmupFn={async () => '/cache/whisper/ggml-tiny.bin'}
      {...extraProps}
    />,
  )
}

describe('RecordingApp menus', () => {
  beforeEach(() => {
    currentController = {
      state: { ...idleState },
      start: vi.fn(),
      stop: vi.fn(() => Promise.resolve()),
      cancel: vi.fn(() => Promise.resolve()),
    }
    exitMock.mockClear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  test('opens the devices menu when d is pressed and selects a device', async () => {
    const { lastFrame, stdin } = renderApp()

    await tick()
    stdin.write('d')
    await tick(10)

    expect(lastFrame()).toContain('Devices')
    expect(lastFrame()).toContain('MacBook Pro Microphone')
    expect(lastFrame()).toContain('External Mic')

    stdin.write('[B')
    await tick()
    stdin.write('\r')
    await tick()

    expect(lastFrame()).toContain('Input device: External Mic')
    expect(lastFrame()).toContain('[r] record')
  })

  test('closes the devices menu on escape without selecting', async () => {
    const { lastFrame, stdin } = renderApp()

    await tick()
    stdin.write('d')
    await tick(10)
    stdin.write('')
    await tick()

    expect(lastFrame()).not.toContain('› MacBook')
    expect(lastFrame()).toContain('[r] record')
  })

  test('opens the model menu when m is pressed and selects a cached model', async () => {
    const { lastFrame, stdin } = renderApp()

    await tick()
    stdin.write('m')
    await tick(10)

    expect(lastFrame()).toContain('Model')
    expect(lastFrame()).toContain('base')

    stdin.write('[B')
    await tick()
    stdin.write('\r')
    await tick()

    expect(lastFrame()).toContain('Model: base')
  })

  test('runs warmup with progress when selecting an uncached model', async () => {
    const runWarmupFn = vi.fn(
      async (_model: string, onProgress: (p: WarmupProgress) => void) => {
        onProgress({ downloaded: 50, total: 100, percent: 50 })
        return '/cache/whisper/ggml-tiny.bin'
      },
    )
    const { lastFrame, stdin } = renderApp({ runWarmupFn })

    await tick()
    stdin.write('m')
    await tick(10)

    // tiny is the first item and is not cached
    stdin.write('\r')
    await tick(10)

    expect(runWarmupFn).toHaveBeenCalledWith('tiny', expect.any(Function))
    expect(lastFrame()).toContain('Model: tiny')
  })

  test('does not quit with q while a menu is open', async () => {
    const { stdin } = renderApp()

    await tick()
    stdin.write('d')
    await tick(10)
    stdin.write('q')
    await tick()

    expect(exitMock).not.toHaveBeenCalled()
  })
})
