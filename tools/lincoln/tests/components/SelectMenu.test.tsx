import { render } from 'ink-testing-library'
import React from 'react'
import { describe, expect, test, vi } from 'vitest'
import { SelectMenu } from '../../src/components/SelectMenu'

async function tick() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

const items = [
  { key: 'a', label: 'Mic A' },
  { key: 'b', label: 'Mic B' },
]

describe('SelectMenu', () => {
  test('renders title and items with the first one selected', () => {
    const { lastFrame } = render(
      <SelectMenu title="Devices" items={items} onSelect={() => {}} onClose={() => {}} />,
    )
    expect(lastFrame()).toContain('Devices')
    expect(lastFrame()).toContain('› Mic A')
    expect(lastFrame()).toContain('  Mic B')
  })

  test('moves selection with the down arrow', async () => {
    const { lastFrame, stdin } = render(
      <SelectMenu title="Devices" items={items} onSelect={() => {}} onClose={() => {}} />,
    )
    await tick()
    stdin.write('[B')
    await tick()
    expect(lastFrame()).toContain('  Mic A')
    expect(lastFrame()).toContain('› Mic B')
  })

  test('calls onSelect with the highlighted key on enter', async () => {
    const onSelect = vi.fn()
    const { stdin } = render(
      <SelectMenu title="Devices" items={items} onSelect={onSelect} onClose={() => {}} />,
    )
    await tick()
    stdin.write('[B')
    await tick()
    stdin.write('\r')
    await tick()
    expect(onSelect).toHaveBeenCalledWith('b')
  })

  test('calls onClose on escape', async () => {
    const onClose = vi.fn()
    const { stdin } = render(
      <SelectMenu title="Devices" items={items} onSelect={() => {}} onClose={onClose} />,
    )
    await tick()
    stdin.write('')
    await tick()
    expect(onClose).toHaveBeenCalledTimes(1)
  })
})
