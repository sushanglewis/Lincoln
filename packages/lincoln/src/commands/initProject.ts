import { readLocalPackageVersion } from '../lib/packageInfo.js'
import { writeProjectMarker, readProjectMarker } from '../lib/marker.js'

export interface InitProjectOptions {
  force?: boolean
  dryRun?: boolean
}

export function initProject(projectRoot: string, options: InitProjectOptions = {}): number {
  if (!options.force && readProjectMarker(projectRoot) !== undefined) {
    console.error(`Project already has a .lincoln.yaml. Use --force to overwrite.`)
    return 1
  }

  try {
    writeProjectMarker(
      projectRoot,
      {
        enabled: true,
        workflow_template: 'interview-to-knowledge',
        min_lincoln_version: readLocalPackageVersion() ?? '1.5.0'
      },
      { force: options.force, dryRun: options.dryRun }
    )
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    console.error(`Failed to write .lincoln.yaml: ${message}`)
    return 1
  }

  if (options.dryRun) {
    console.log(`Dry run: would create ${projectRoot}/.lincoln.yaml`)
  } else {
    console.log(`Created ${projectRoot}/.lincoln.yaml`)
  }
  return 0
}
