import { Text } from 'ink'
import { render } from 'ink-testing-library'
import React, { useState } from 'react'
import { describe, expect, test, vi } from 'vitest'
import { useKeyHandler } from '../../src/hooks/useKeyHandler'

function TestComponent({ onStop, onCancel }: { onStop: () => void; onCancel: () => void }) {
  useKeyHandler({ onStop, onCancel })
  const [count, setCount] = useState(0)
  return <Text onClick={() => setCount(c => c + 1)}>{count}</Text>
}

async function tick() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

describe('useKeyHandler', () => {
  test('calls onStop when Enter is pressed', async () => {
    const onStop = vi.fn()
    const onCancel = vi.fn()
    const { stdin } = render(<TestComponent onStop={onStop} onCancel={onCancel} />)

    await tick()
    stdin.write('\r')
    await tick()

    expect(onStop).toHaveBeenCalledTimes(1)
    expect(onCancel).not.toHaveBeenCalled()
  })

  test('calls onCancel when q is pressed', async () => {
    const onStop = vi.fn()
    const onCancel = vi.fn()
    const { stdin } = render(<TestComponent onStop={onStop} onCancel={onCancel} />)

    await tick()
    stdin.write('q')
    await tick()

    expect(onCancel).toHaveBeenCalledTimes(1)
    expect(onStop).not.toHaveBeenCalled()
  })
})
