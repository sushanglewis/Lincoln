import { describe, it, expect } from 'vitest'
import { runPostinstall } from '../src/postinstall.js'

describe('runPostinstall', () => {
  it('exits 0 in CI without writing', () => {
    process.env.CI = 'true'
    expect(runPostinstall()).toBe(0)
    delete process.env.CI
  })

  it('exits 0 in test environment without writing', () => {
    process.env.NODE_ENV = 'test'
    expect(runPostinstall()).toBe(0)
    delete process.env.NODE_ENV
  })
})
