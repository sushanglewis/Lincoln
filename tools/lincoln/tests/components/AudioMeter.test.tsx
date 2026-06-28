import { render } from 'ink-testing-library'
import React from 'react'
import { describe, expect, test } from 'vitest'
import { AudioMeter } from '../../src/components/AudioMeter'

describe('AudioMeter', () => {
  test('renders bar style with correct number of blocks', () => {
    const { lastFrame } = render(<AudioMeter amplitude={0.5} style="bar" />)

    expect(lastFrame()).toContain('█')
    expect(lastFrame()?.length).toBeGreaterThan(0)
  })

  test('renders dot style', () => {
    const { lastFrame } = render(<AudioMeter amplitude={0.5} style="dot" />)

    expect(lastFrame()).toContain('●')
  })

  test('renders wave style', () => {
    const { lastFrame } = render(<AudioMeter amplitude={0.5} style="wave" />)

    expect(lastFrame()).toContain('~')
  })

  test('renders empty meter for zero amplitude', () => {
    const { lastFrame } = render(<AudioMeter amplitude={0} style="bar" />)

    expect(lastFrame()).not.toContain('█')
  })
})
