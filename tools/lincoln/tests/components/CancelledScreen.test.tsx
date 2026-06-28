import { render } from 'ink-testing-library'
import React from 'react'
import { describe, expect, test } from 'vitest'
import { CancelledScreen } from '../../src/components/CancelledScreen'

describe('CancelledScreen', () => {
  test('renders cancellation message', () => {
    const { lastFrame } = render(<CancelledScreen />)

    expect(lastFrame()).toContain('cancelled')
  })
})
