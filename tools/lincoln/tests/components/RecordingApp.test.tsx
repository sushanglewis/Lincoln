import { render } from 'ink-testing-library'
import React from 'react'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import { RecordingApp } from '../../src/components/RecordingApp'
import type { RecorderController, RecorderState } from '../../src/recording/useRecorder'

const baseController: RecorderController = {
  state: {
    status: 'recording',
    duration: 83,
    amplitude: 0.65,
    errorMessage: null,
  },
  start: vi.fn(),
  stop: vi.fn(),
  cancel: vi.fn(),
}

let currentController = { ...baseController }

vi.mock('../../src/recording/useRecorder', () => ({
  useRecorder: vi.fn(() => currentController),
}))

async function tick() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

describe('RecordingApp', () => {
  beforeEach(() => {
    currentController = {
      state: { status: 'recording', duration: 83, amplitude: 0.65, errorMessage: null },
      start: vi.fn(),
      stop: vi.fn(),
      cancel: vi.fn(),
    }
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  test('renders recording screen with session info', () => {
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

    expect(lastFrame()).toContain('2026-06-28-test')
    expect(lastFrame()).toContain('测试访谈')
    expect(lastFrame()).toContain('Recording')
    expect(lastFrame()).toContain('01:23')
  })

  test('shows cancelled screen', () => {
    currentController.state = { status: 'cancelled', duration: 0, amplitude: 0, errorMessage: null }

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

    expect(lastFrame()).toContain('cancelled')
  })

  test('shows stopped screen', () => {
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

    expect(lastFrame()).toContain('Stopped')
  })

  test('calls stop when Enter is pressed', async () => {
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
    stdin.write('\r')
    await tick()

    expect(currentController.stop).toHaveBeenCalled()
  })

  test('calls cancel when q is pressed', async () => {
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

    expect(currentController.cancel).toHaveBeenCalled()
  })
})
