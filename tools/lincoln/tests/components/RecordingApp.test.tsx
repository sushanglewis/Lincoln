import { render } from 'ink-testing-library'
import React from 'react'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import { RecordingApp } from '../../src/components/RecordingApp'
import type { RecorderController, RecorderState } from '../../src/recording/useRecorder'

const idleState: RecorderState = {
  status: 'idle',
  duration: 0,
  amplitude: 0,
  errorMessage: null,
}

const recordingState: RecorderState = {
  status: 'recording',
  duration: 83,
  amplitude: 0.65,
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

async function tick() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

describe('RecordingApp', () => {
  beforeEach(() => {
    currentController = {
      state: { ...idleState },
      start: vi.fn(() => {
        currentController.state = { ...recordingState }
      }),
      stop: vi.fn(() => {
        currentController.state = { status: 'stopped', duration: 83, amplitude: 0, errorMessage: null }
        return Promise.resolve()
      }),
      cancel: vi.fn(() => {
        currentController.state = { status: 'cancelled', duration: 0, amplitude: 0, errorMessage: null }
        return Promise.resolve()
      }),
    }
    exitMock.mockClear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  test('renders single HUD initially', () => {
    const { lastFrame } = render(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic="测试访谈"
        designId="test-design"
        branch="main"
        audioMeterStyle="bar"
      />,
    )

    expect(lastFrame()).toContain('Lincoln Recorder')
    expect(lastFrame()).toContain('Session: 2026-06-28-test')
    expect(lastFrame()).toContain('Topic: 测试访谈')
    expect(lastFrame()).toContain('[r] record  [d] devices  [m] model  [q] quit')
  })

  test('starts recording when r is pressed', async () => {
    const { stdin } = render(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )

    await tick()
    stdin.write('r')
    await tick()

    expect(currentController.start).toHaveBeenCalled()
  })

  test('exits when q is pressed from idle', async () => {
    const { stdin } = render(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )

    await tick()
    stdin.write('q')
    await tick()

    expect(exitMock).toHaveBeenCalled()
    expect(currentController.start).not.toHaveBeenCalled()
  })

  test('calls stop when s is pressed during recording', async () => {
    const { stdin, rerender } = render(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )

    await tick()
    stdin.write('r')
    await tick()
    expect(currentController.start).toHaveBeenCalled()

    rerender(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )
    await tick()

    stdin.write('s')
    await tick()

    expect(currentController.stop).toHaveBeenCalled()
  })

  test('calls cancel and exits when c is pressed during recording', async () => {
    const { stdin, rerender } = render(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )

    await tick()
    stdin.write('r')
    await tick()

    rerender(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )
    await tick()

    stdin.write('c')
    await tick()

    expect(currentController.cancel).toHaveBeenCalled()
  })

  test('shows stopped summary when stopped', async () => {
    currentController.state = { status: 'stopped', duration: 120, amplitude: 0, errorMessage: null }

    const { lastFrame } = render(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )

    await tick()
    expect(lastFrame()).toContain('Stopped')
    expect(lastFrame()).toContain('claude process-interview 2026-06-28-test')
    expect(lastFrame()).toContain('[any key] exit')
  })

  test('exits when any key is pressed on stopped screen', async () => {
    currentController.state = { status: 'stopped', duration: 120, amplitude: 0, errorMessage: null }

    const { stdin } = render(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )

    await tick()
    stdin.write('y')
    await tick()

    expect(exitMock).toHaveBeenCalled()
  })

  test('logs error when recorder fails', async () => {
    currentController.state = { status: 'error', duration: 0, amplitude: 0, errorMessage: 'microphone not found' }

    const { lastFrame } = render(
      <RecordingApp
        workspaceRoot="/workspace"
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        branch=""
        audioMeterStyle="bar"
      />,
    )

    await tick()
    expect(lastFrame()).toContain('microphone not found')
    expect(lastFrame()).toContain('[q] exit')
  })
})
