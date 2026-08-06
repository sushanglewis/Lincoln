const SEMVER_CORE = /^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$/
const NUMERIC_IDENTIFIER = /^\d+$/

interface ParsedVersion {
  major: number
  minor: number
  patch: number
  prerelease: string[]
}

/**
 * Compares two semver strings per semver.org precedence rules (build metadata
 * ignored). Returns a negative number when a < b, 0 when equal, a positive
 * number when a > b, or undefined when either input is not a parseable semver.
 */
export function compareVersions(a: string, b: string): number | undefined {
  const pa = parseVersion(a)
  const pb = parseVersion(b)
  if (!pa || !pb) {
    return undefined
  }
  if (pa.major !== pb.major) return pa.major - pb.major
  if (pa.minor !== pb.minor) return pa.minor - pb.minor
  if (pa.patch !== pb.patch) return pa.patch - pb.patch
  return comparePrerelease(pa.prerelease, pb.prerelease)
}

function parseVersion(version: string): ParsedVersion | undefined {
  const match = SEMVER_CORE.exec(version.trim())
  if (!match) {
    return undefined
  }
  return {
    major: Number(match[1]),
    minor: Number(match[2]),
    patch: Number(match[3]),
    prerelease: match[4] ? match[4].split('.') : []
  }
}

function comparePrerelease(a: string[], b: string[]): number {
  if (a.length === 0 && b.length === 0) return 0
  // A version without a prerelease has higher precedence than one with it.
  if (a.length === 0) return 1
  if (b.length === 0) return -1
  const shared = Math.min(a.length, b.length)
  for (let i = 0; i < shared; i++) {
    const x = a[i]
    const y = b[i]
    if (x === y) continue
    const xNumeric = NUMERIC_IDENTIFIER.test(x)
    const yNumeric = NUMERIC_IDENTIFIER.test(y)
    if (xNumeric && yNumeric) return Number(x) - Number(y)
    // Numeric identifiers have lower precedence than alphanumeric ones.
    if (xNumeric) return -1
    if (yNumeric) return 1
    return x < y ? -1 : 1
  }
  return a.length - b.length
}
