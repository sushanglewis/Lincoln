import { describe, it, expect } from 'vitest'
import { resolveLincolnPaths } from '../../src/lib/paths.js'

describe('resolveLincolnPaths', () => {
  it('resolves ~/.lincoln/current', () => {
    const p = resolveLincolnPaths('/tmp/home')
    expect(p.currentDir).toBe('/tmp/home/.lincoln/current')
  })

  it('respects LINCOLN_HOME override', () => {
    process.env.LINCOLN_HOME = '/opt/lincoln'
    const p = resolveLincolnPaths('/tmp/home')
    expect(p.lincolnHome).toBe('/opt/lincoln')
    expect(p.currentDir).toBe('/opt/lincoln/current')
    delete process.env.LINCOLN_HOME
  })

  it('resolves harness config directories', () => {
    const p = resolveLincolnPaths('/tmp/home')
    expect(p.claudeDir).toBe('/tmp/home/.claude')
    expect(p.codexDir).toBe('/tmp/home/.codex')
    expect(p.opencodeDir).toBe('/tmp/home/.opencode')
  })
})
