import { render } from 'ink-testing-library'
import React from 'react'
import { describe, expect, test } from 'vitest'
import { App } from '../src/cli'

const baseConfig = {
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
