import { describe, it, expect } from 'vitest'
import { compareVersions } from '../../src/lib/semver.js'

describe('compareVersions', () => {
  it('returns 0 for equal versions', () => {
    expect(compareVersions('1.6.0', '1.6.0')).toBe(0)
  })

  it('tolerates a leading v prefix', () => {
    expect(compareVersions('v1.6.0', '1.6.0')).toBe(0)
  })

  it('ignores build metadata', () => {
    expect(compareVersions('1.6.0+build.1', '1.6.0')).toBe(0)
  })

  it('orders by major, then minor, then patch', () => {
    expect(compareVersions('2.0.0', '1.9.9')).toBeGreaterThan(0)
    expect(compareVersions('1.5.0', '1.6.0')).toBeLessThan(0)
    expect(compareVersions('1.6.1', '1.6.0')).toBeGreaterThan(0)
  })

  it('ranks a prerelease below its release', () => {
    expect(compareVersions('2.0.0-beta.1', '2.0.0')).toBeLessThan(0)
    expect(compareVersions('2.0.0', '2.0.0-beta.1')).toBeGreaterThan(0)
  })

  it('ranks a prerelease above an older release', () => {
    expect(compareVersions('2.0.0-beta.1', '1.6.0')).toBeGreaterThan(0)
  })

  it('compares prerelease identifiers numerically when both are numeric', () => {
    expect(compareVersions('1.0.0-alpha.2', '1.0.0-alpha.10')).toBeLessThan(0)
  })

  it('ranks numeric prerelease identifiers below alphanumeric ones', () => {
    expect(compareVersions('1.0.0-1', '1.0.0-alpha')).toBeLessThan(0)
  })

  it('ranks a shorter prerelease list below a longer one with a shared prefix', () => {
    expect(compareVersions('1.0.0-alpha', '1.0.0-alpha.1')).toBeLessThan(0)
  })

  it('compares alphanumeric prerelease identifiers lexically', () => {
    expect(compareVersions('1.0.0-alpha', '1.0.0-beta')).toBeLessThan(0)
  })

  it('returns undefined when either side is not a semver', () => {
    expect(compareVersions('latest', '1.6.0')).toBeUndefined()
    expect(compareVersions('1.6.0', 'not-a-version')).toBeUndefined()
  })
})
