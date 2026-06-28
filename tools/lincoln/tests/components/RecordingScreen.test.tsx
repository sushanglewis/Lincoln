import { render } from 'ink-testing-library'
import React from 'react'
import { describe, expect, test } from 'vitest'
import { RecordingScreen } from '../../src/components/RecordingScreen'

describe('RecordingScreen', () => {
  test('renders session info and recording status', () => {
    const { lastFrame } = render(
      <RecordingScreen
        sessionId="2026-06-28-test"
        topic="测试访谈"
        designId="test-design"
        duration={83}
        amplitude={0.65}
      />,
    )

    expect(lastFrame()).toContain('2026-06-28-test')
    expect(lastFrame()).toContain('测试访谈')
    expect(lastFrame()).toContain('Recording')
    expect(lastFrame()).toContain('01:23')
  })

  test('renders audio meter when enabled', () => {
    const { lastFrame } = render(
      <RecordingScreen
        sessionId="2026-06-28-test"
        topic=""
        designId=""
        duration={0}
        amplitude={0.8}
      />,
    )

    expect(lastFrame()).toContain('█')
  })
})
