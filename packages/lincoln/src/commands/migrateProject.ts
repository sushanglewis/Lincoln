import fs from 'node:fs'
import path from 'node:path'
import { listVendoredFrameworkFiles } from '../lib/projectFiles.js'
import { readLocalPackageVersion } from '../lib/packageInfo.js'
import { writeProjectMarker } from '../lib/marker.js'
import { resolveLincolnPaths } from '../lib/paths.js'
import type { LincolnPaths } from '../lib/paths.js'

export interface MigrateProjectOptions {
  dryRun?: boolean
  yes?: boolean
  force?: boolean
}

export interface MigrateProjectDeps {
  paths: LincolnPaths
  listVendoredFrameworkFiles: (
    payloadRoot: string,
    projectRoot: string
  ) => ReturnType<typeof listVendoredFrameworkFiles>
  writeProjectMarker: typeof writeProjectMarker
}

export function createDefaultDeps(): MigrateProjectDeps {
  return {
    paths: resolveLincolnPaths(),
    listVendoredFrameworkFiles,
    writeProjectMarker
  }
}

export async function migrateProject(
  projectRoot: string,
  options: MigrateProjectOptions = {},
  deps: MigrateProjectDeps = createDefaultDeps()
): Promise<number> {
  const payloadRoot = deps.paths.currentDir
  if (!fs.existsSync(payloadRoot)) {
    console.error(`Lincoln payload not found at ${payloadRoot}. Run "lincoln install" first.`)
    return 1
  }

  const absoluteProjectRoot = path.resolve(projectRoot)
  const report = deps.listVendoredFrameworkFiles(payloadRoot, absoluteProjectRoot)

  if (options.dryRun) {
    console.log(`Dry run: would migrate ${absoluteProjectRoot}`)
    if (report.removable.length > 0) {
      console.log('Would remove unmodified framework files:')
      for (const f of report.removable) console.log(`  - ${f}`)
    }
    if (report.modified.length > 0) {
      console.log('Would preserve modified framework files:')
      for (const f of report.modified) console.log(`  - ${f}`)
    }
    if (report.preserved.length > 0) {
      console.log('Would preserve project-local files:')
      for (const f of report.preserved) console.log(`  - ${f}`)
    }
    console.log('Would create .lincoln.yaml')
    return 0
  }

  if (!options.yes) {
    console.error('This will remove vendored framework files. Run with --yes to proceed.')
    return 1
  }

  for (const file of report.removable) {
    const filePath = path.join(absoluteProjectRoot, file)
    try {
      fs.rmSync(filePath)
      // Remove empty parent directories up to project root
      let dir = path.dirname(filePath)
      while (dir !== absoluteProjectRoot && fs.existsSync(dir)) {
        const entries = fs.readdirSync(dir)
        if (entries.length === 0) {
          fs.rmdirSync(dir)
          dir = path.dirname(dir)
        } else {
          break
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      console.error(`Failed to remove ${file}: ${message}`)
      return 1
    }
  }

  if (report.modified.length > 0) {
    console.log('Preserved modified framework files:')
    for (const f of report.modified) console.log(`  - ${f}`)
  }

  if (report.preserved.length > 0) {
    console.log('Preserved project-local files:')
    for (const f of report.preserved) console.log(`  - ${f}`)
  }

  try {
    deps.writeProjectMarker(
      absoluteProjectRoot,
      {
        enabled: true,
        workflow_template: 'interview-to-knowledge',
        min_lincoln_version: readLocalPackageVersion() ?? '1.5.0'
      },
      { force: options.force }
    )
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    console.error(`Failed to write .lincoln.yaml: ${message}`)
    return 1
  }

  console.log(`Migrated project at ${absoluteProjectRoot}`)
  console.log(`Removed ${report.removable.length} unmodified framework files`)
  return 0
}
