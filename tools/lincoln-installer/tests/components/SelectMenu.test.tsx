import React from 'react'
import { describe, expect, test, vi } from 'vitest'
import { render } from 'ink-testing-library'
import { SelectMenu } from '../../src/components/SelectMenu'

describe('SelectMenu', () => {
  test('renders items and marks selected', () => {
    const onSelect = vi.fn()
    const onConfirm = vi.fn()
    const { lastFrame } = render(
      <SelectMenu
        title="Choose"
        items={[
          { label: 'One', value: 'one' },
          { label: 'Two', value: 'two' },
        ]}
        selected={['one']}
        onSelect={onSelect}
        onConfirm={onConfirm}
      />
    )
    const frame = lastFrame() ?? ''
    expect(frame).toContain('One')
    expect(frame).toContain('Two')
  })
})
