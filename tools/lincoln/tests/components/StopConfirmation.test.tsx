import { render } from 'ink-testing-library'
import React from 'react'
import { describe, expect, test, vi } from 'vitest'
import { StopConfirmation } from '../../src/components/StopConfirmation'

async function tick() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

describe('StopConfirmation', () => {
  test('renders prompt and options', () => {
    const { lastFrame } = render(<StopConfirmation sessionId="2026-06-28-test" onConfirm={vi.fn()} onCancel={vi.fn()} />,
    )

    expect(lastFrame()).toContain('process-interview')
    expect(lastFrame()).toContain('Yes')
    expect(lastFrame()).toContain('No')
  })

  test('calls onConfirm when y is pressed', async () => {
    const onConfirm = vi.fn()
    const onCancel = vi.fn()
    const { stdin } = render(<StopConfirmation sessionId="2026-06-28-test" onConfirm={onConfirm} onCancel={onCancel} />,
    )

    await tick()
    stdin.write('y')
    await tick()

    expect(onConfirm).toHaveBeenCalledTimes(1)
    expect(onCancel).not.toHaveBeenCalled()
  })

  test('calls onCancel when n is pressed', async () => {
    const onConfirm = vi.fn()
    const onCancel = vi.fn()
    const { stdin } = render(<StopConfirmation sessionId="2026-06-28-test" onConfirm={onConfirm} onCancel={onCancel} />,
    )

    await tick()
    stdin.write('n')
    await tick()

    expect(onCancel).toHaveBeenCalledTimes(1)
    expect(onConfirm).not.toHaveBeenCalled()
  })
})
