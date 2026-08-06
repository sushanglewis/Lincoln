import fs from 'node:fs'
import path from 'node:path'
import yaml from 'js-yaml'

export interface ProjectMarker {
  enabled: boolean
  workflow_template?: string
  min_lincoln_version?: string
}

export interface WriteMarkerOptions {
  force?: boolean
  dryRun?: boolean
}

export function readProjectMarker(projectRoot: string): ProjectMarker | undefined {
  const markerPath = path.join(projectRoot, '.lincoln.yaml')
  if (!fs.existsSync(markerPath)) {
    return undefined
  }
  try {
    const parsed = yaml.load(fs.readFileSync(markerPath, 'utf8')) as Record<string, unknown> | null | undefined
    if (!parsed || typeof parsed !== 'object') {
      return undefined
    }
    return {
      enabled: Boolean(parsed.enabled),
      workflow_template: typeof parsed.workflow_template === 'string' ? parsed.workflow_template : undefined,
      min_lincoln_version: typeof parsed.min_lincoln_version === 'string' ? parsed.min_lincoln_version : undefined
    }
  } catch {
    return undefined
  }
}

export function writeProjectMarker(
  projectRoot: string,
  marker: ProjectMarker,
  opts: WriteMarkerOptions = {}
): void {
  const markerPath = path.join(projectRoot, '.lincoln.yaml')
  if (fs.existsSync(markerPath) && !opts.force) {
    throw new Error(`.lincoln.yaml already exists at ${markerPath}; use --force to overwrite`)
  }
  const content = yaml.dump(marker, { sortKeys: false, lineWidth: -1 })
  if (!opts.dryRun) {
    fs.mkdirSync(projectRoot, { recursive: true })
    fs.writeFileSync(markerPath, content)
  }
}
