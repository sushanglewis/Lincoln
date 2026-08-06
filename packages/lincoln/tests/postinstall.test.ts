import { describe, it, expect } from 'vitest'
import { runPostinstall } from '../src/postinstall.js'

describe('runPostinstall', () => {
  it('exits 0 in CI without writing', async () => {
    process.env.CI = 'true'
    expect(await runPostinstall()).toBe(0)
    delete process.env.CI
  })

  it('exits 0 in test environment without writing', async () => {
    process.env.NODE_ENV = 'test'
    expect(await runPostinstall()).toBe(0)
    delete process.env.NODE_ENV
  })

  it('exits 0 when stdin is not a TTY', async () => {
    const deps = {
      isTTY: false,
      confirm: async () => true,
      install: async () => 0,
      env: {}
    }
    expect(await runPostinstall(deps)).toBe(0)
  })

  it('exits 0 even when interactive install throws', async () => {
    const deps = {
      isTTY: true,
      confirm: async () => true,
      install: async () => {
        throw new Error('boom')
      },
      env: {}
    }
    expect(await runPostinstall(deps)).toBe(0)
  })

  it('runs interactive install when user confirms', async () => {
    let called = false
    const deps = {
      isTTY: true,
      confirm: async () => true,
      install: async () => {
        called = true
        return 0
      },
      env: {}
    }
    expect(await runPostinstall(deps)).toBe(0)
    expect(called).toBe(true)
  })

  it('skips install when user declines', async () => {
    let called = false
    const deps = {
      isTTY: true,
      confirm: async () => false,
      install: async () => {
        called = true
        return 0
      },
      env: {}
    }
    expect(await runPostinstall(deps)).toBe(0)
    expect(called).toBe(false)
  })
})
