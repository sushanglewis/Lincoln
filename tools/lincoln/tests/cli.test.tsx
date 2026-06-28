import { render } from 'ink-testing-library'
import React from 'react'
import { describe, expect, test, vi } from 'vitest'
import { App } from '../src/cli'

vi.mock('../src/recording/useRecorder', () => ({
  useRecorder: vi.fn(() => ({
    state: { status: 'recording', duration: 0, amplitude: 0.3, errorMessage: null },
    start: vi.fn(),
    stop: vi.fn(),
    cancel: vi.fn(),
  })),
}))

const baseConfig = {
  workspaceRoot: '/workspace',
  topic: '',
  designId: '',
  branch: '',
  sessionId: '2026-06-28-test',
  noTui: false,
  autoProcess: false,
  showAudioMeter: true,
  audioMeterStyle: 'bar' as const,
}

describe('App', () => {
  test('renders help when help arg is true', () => {
    const { lastFrame } = render(<App args={{ help: true, noTui: false }} config={baseConfig} />,
    )

    expect(lastFrame()).toContain('Usage:')
  })

  test('renders recording app when help is false', () => {
    const { lastFrame } = render(
      <App
        args={{ help: false, noTui: false }}
        config={{
          ...baseConfig,
          topic: '测试',
          designId: 'test-design',
          branch: 'main',
        }}
      />,
    )

    expect(lastFrame()).toContain('Lincoln Recorder')
    expect(lastFrame()).toContain('2026-06-28-test')
    expect(lastFrame()).toContain('测试')
  })
})
