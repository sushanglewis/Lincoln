import { render } from 'ink-testing-library'
import React from 'react'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import { RecordingApp } from '../../src/components/RecordingApp'

async function realTick() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

describe('RecordingApp', () => {
  describe('with real timers', () => {
    test('renders recording screen with session info', () => {
      const { lastFrame } = render(
        <RecordingApp
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
    })

    test('shows cancelled screen when q is pressed', async () => {
      const { lastFrame, stdin } = render(
        <RecordingApp
          sessionId="2026-06-28-test"
          topic=""
          designId=""
          branch=""
          audioMeterStyle="bar"
        />,
      )

      await realTick()
      stdin.write('q')
      await realTick()

      expect(lastFrame()).toContain('cancelled')
    })

    test('stops recording when Enter is pressed', async () => {
      const { lastFrame, stdin } = render(
        <RecordingApp
          sessionId="2026-06-28-test"
          topic=""
          designId=""
          branch=""
          audioMeterStyle="bar"
        />,
      )

      await realTick()
      stdin.write('\r')
      await realTick()

      expect(lastFrame()).toContain('Stopped')
    })
  })

  describe('with fake timers', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    test('increments duration over time', async () => {
      const { lastFrame } = render(
        <RecordingApp
          sessionId="2026-06-28-test"
          topic=""
          designId=""
          branch=""
          audioMeterStyle="bar"
        />,
      )

      expect(lastFrame()).toContain('00:00')
      await vi.advanceTimersByTimeAsync(3500)
      expect(lastFrame()).toContain('00:03')
    })
  })
})
