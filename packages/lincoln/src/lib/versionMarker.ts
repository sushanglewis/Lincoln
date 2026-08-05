import fs from 'node:fs'
import path from 'node:path'
import type { LincolnPaths } from './paths.js'

export interface VersionMarker {
  version: string
  installedAt: string
  harnesses: string[]
  managedFiles: string[]
}

export function readVersionMarker(paths: LincolnPaths): VersionMarker | undefined {
  try {
    const raw = fs.readFileSync(paths.versionMarker, 'utf8')
    const parsed = JSON.parse(raw) as VersionMarker
    if (
      typeof parsed.version === 'string' &&
      typeof parsed.installedAt === 'string' &&
      Array.isArray(parsed.harnesses)
    ) {
      return parsed
    }
    return undefined
  } catch {
    return undefined
  }
}

export function writeVersionMarker(
  paths: LincolnPaths,
  marker: VersionMarker
): void {
  fs.mkdirSync(path.dirname(paths.versionMarker), { recursive: true })
  fs.writeFileSync(paths.versionMarker, JSON.stringify(marker, null, 2) + '\n')
}

export function isUpToDate(paths: LincolnPaths, version: string): boolean {
  const marker = readVersionMarker(paths)
  return marker?.version === version
}
