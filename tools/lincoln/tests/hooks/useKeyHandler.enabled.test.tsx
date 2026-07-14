import { Text } from 'ink'
import { render } from 'ink-testing-library'
import React from 'react'
import { describe, expect, test, vi } from 'vitest'
import { useKeyHandler } from '../../src/hooks/useKeyHandler'

const onRecordMock = vi.fn()
const onQuitMock = vi.fn()

function TestComponent({ enabled }: { enabled: boolean }) {
  useKeyHandler({ enabled, onRecord: onRecordMock, onQuit: onQuitMock })
  return <Text>handlers active</Text>
}

async function tick() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

describe('useKeyHandler enabled flag', () => {
  test('ignores all keys when disabled', async () => {
    onRecordMock.mockClear()
    onQuitMock.mockClear()
    const { stdin } = render(<TestComponent enabled={false} />)

    await tick()
    stdin.write('r')
    stdin.write('q')
    await tick()

    expect(onRecordMock).not.toHaveBeenCalled()
    expect(onQuitMock).not.toHaveBeenCalled()
  })

  test('handles keys when enabled', async () => {
    onRecordMock.mockClear()
    const { stdin } = render(<TestComponent enabled />)

    await tick()
    stdin.write('r')
    await tick()

    expect(onRecordMock).toHaveBeenCalledTimes(1)
  })
})
