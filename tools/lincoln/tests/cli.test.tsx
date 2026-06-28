import { render } from 'ink-testing-library'
import React from 'react'
import { describe, expect, test } from 'vitest'
import { App } from '../src/cli'

describe('App', () => {
  test('renders help when help arg is true', () => {
    const { lastFrame } = render(
      <App args={{ help: true, noTui: false }} config={{ topic: '', designId: '', branch: '', sessionId: '2026-06-28-test', noTui: false, autoProcess: false, showAudioMeter: true, audioMeterStyle: 'bar' }} />,
    )

    expect(lastFrame()).toContain('Usage:')
  })

  test('renders welcome message when help is false', () => {
    const { lastFrame } = render(
      <App
        args={{ help: false, noTui: false }}
        config={{ topic: '测试', designId: 'test-design', branch: 'main', sessionId: '2026-06-28-test', noTui: false, autoProcess: false, showAudioMeter: true, audioMeterStyle: 'bar' }}
      />,
    )

    expect(lastFrame()).toContain('Lincoln')
  })
})
