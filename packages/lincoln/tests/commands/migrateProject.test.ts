import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { migrateProject, createDefaultDeps } from '../../src/commands/migrateProject.js'
import type { VendoredFileReport } from '../../src/lib/projectFiles.js'
import type { LincolnPaths } from '../../src/lib/paths.js'

describe('migrateProject', () => {
  let tmpDir: string

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lincoln-migrate-test-'))
  })

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true })
  })

  function makeDeps(report: VendoredFileReport) {
    const projectMarkerPath = path.join(tmpDir, '.lincoln.yaml')
    const paths: LincolnPaths = {
      homeDir: tmpDir,
      lincolnDir: path.join(tmpDir, '.lincoln'),
      versionsDir: path.join(tmpDir, '.lincoln', 'versions'),
      currentDir: path.join(tmpDir, '.lincoln', 'current'),
      claudeDir: path.join(tmpDir, '.claude'),
      versionMarkerFile: path.join(tmpDir, '.lincoln', 'marker.json')
    }
    fs.mkdirSync(paths.currentDir, { recursive: true })
    return {
      paths,
      listVendoredFrameworkFiles: () => report,
      writeProjectMarker: (root: string, marker: object, opts: { force?: boolean }) => {
        if (!opts.force && fs.existsSync(projectMarkerPath)) {
          throw new Error('.lincoln.yaml already exists')
        }
        fs.writeFileSync(path.join(root, '.lincoln.yaml'), 'enabled: true\n', 'utf8')
      }
    }
  }

  it('lists unmodified framework files for removal in dry-run', async () => {
    const project = path.join(tmpDir, 'project')
    fs.mkdirSync(project, { recursive: true })
    const report: VendoredFileReport = {
      removable: [path.join('.claude', 'stages', 'clarify.yaml')],
      modified: [],
      preserved: []
    }
    const code = await migrateProject(project, { dryRun: true, yes: false, force: false }, makeDeps(report))
    expect(code).toBe(0)
    expect(fs.existsSync(path.join(project, '.lincoln.yaml'))).toBe(false)
  })

  it('removes unmodified files when --yes is provided', async () => {
    const project = path.join(tmpDir, 'project')
    const filePath = path.join(project, '.claude', 'stages', 'clarify.yaml')
    fs.mkdirSync(path.dirname(filePath), { recursive: true })
    fs.writeFileSync(filePath, 'stage: clarify\n')

    const report: VendoredFileReport = {
      removable: [path.join('.claude', 'stages', 'clarify.yaml')],
      modified: [],
      preserved: []
    }
    const code = await migrateProject(project, { dryRun: false, yes: true, force: false }, makeDeps(report))
    expect(code).toBe(0)
    expect(fs.existsSync(filePath)).toBe(false)
    expect(fs.existsSync(path.join(project, '.lincoln.yaml'))).toBe(true)
  })

  it('refuses to migrate without --yes in non-dry-run', async () => {
    const project = path.join(tmpDir, 'project')
    fs.mkdirSync(project, { recursive: true })
    const report: VendoredFileReport = { removable: [], modified: [], preserved: [] }
    const code = await migrateProject(project, { dryRun: false, yes: false, force: false }, makeDeps(report))
    expect(code).toBe(1)
    expect(fs.existsSync(path.join(project, '.lincoln.yaml'))).toBe(false)
  })
})
