import { Text } from 'ink'
import { render } from 'ink-testing-library'
import React from 'react'
import { describe, expect, test } from 'vitest'
import { useRecorder } from '../../src/recording/useRecorder'

function TestApp() {
  const { state } = useRecorder({
    workspaceRoot: '/workspace',
    sessionId: '2026-06-28-test',
    topic: '',
    designId: '',
    branch: '',
    startOnMount: false,
  })
  return <Text>{state.status}</Text>
}

describe('useRecorder', () => {
  test('starts in idle state', () => {
    const { lastFrame } = render(<TestApp />)

    expect(lastFrame()).toBe('idle')
  })
})
