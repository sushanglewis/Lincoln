import { Text } from 'ink'
import { render } from 'ink-testing-library'
import React from 'react'
import { describe, expect, test, vi } from 'vitest'
import { useKeyHandler } from '../../src/hooks/useKeyHandler'

interface TestComponentProps {
  onRecord?: () => void
  onStop?: () => void
  onCancel?: () => void
  onQuit?: () => void
  onDevices?: () => void
  onModel?: () => void
  onAnyKey?: () => void
}

function TestComponent(props: TestComponentProps) {
  useKeyHandler(props)
  return <Text>handlers active</Text>
}

async function tick() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

describe('useKeyHandler', () => {
  test('calls onRecord when r is pressed', async () => {
    const onRecord = vi.fn()
    const { stdin } = render(
      <TestComponent onRecord={onRecord} />,
    )

    await tick()
    stdin.write('r')
    await tick()

    expect(onRecord).toHaveBeenCalledTimes(1)
  })

  test('calls onStop when s is pressed', async () => {
    const onStop = vi.fn()
    const { stdin } = render(
      <TestComponent onStop={onStop} />,
    )

    await tick()
    stdin.write('s')
    await tick()

    expect(onStop).toHaveBeenCalledTimes(1)
  })

  test('calls onCancel when c is pressed', async () => {
    const onCancel = vi.fn()
    const { stdin } = render(
      <TestComponent onCancel={onCancel} />,
    )

    await tick()
    stdin.write('c')
    await tick()

    expect(onCancel).toHaveBeenCalledTimes(1)
  })

  test('calls onQuit when q is pressed', async () => {
    const onQuit = vi.fn()
    const { stdin } = render(
      <TestComponent onQuit={onQuit} />,
    )

    await tick()
    stdin.write('q')
    await tick()

    expect(onQuit).toHaveBeenCalledTimes(1)
  })

  test('calls onQuit when Escape is pressed', async () => {
    const onQuit = vi.fn()
    const { stdin } = render(
      <TestComponent onQuit={onQuit} />,
    )

    await tick()
    stdin.write('')
    await tick()

    expect(onQuit).toHaveBeenCalledTimes(1)
  })

  test('calls onDevices when d is pressed', async () => {
    const onDevices = vi.fn()
    const { stdin } = render(
      <TestComponent onDevices={onDevices} />,
    )

    await tick()
    stdin.write('d')
    await tick()

    expect(onDevices).toHaveBeenCalledTimes(1)
  })

  test('calls onModel when m is pressed', async () => {
    const onModel = vi.fn()
    const { stdin } = render(
      <TestComponent onModel={onModel} />,
    )

    await tick()
    stdin.write('m')
    await tick()

    expect(onModel).toHaveBeenCalledTimes(1)
  })

  test('calls onAnyKey for unrecognized input', async () => {
    const onAnyKey = vi.fn()
    const { stdin } = render(
      <TestComponent onAnyKey={onAnyKey} />,
    )

    await tick()
    stdin.write('x')
    await tick()

    expect(onAnyKey).toHaveBeenCalledTimes(1)
  })
})
