import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { initProject } from '../../src/commands/initProject.js'

describe('initProject', () => {
  let tmpDir: string

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lincoln-init-test-'))
  })

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true })
  })

  it('creates .lincoln.yaml', () => {
    const code = initProject(tmpDir, { force: false, dryRun: false })
    expect(code).toBe(0)
    const content = fs.readFileSync(path.join(tmpDir, '.lincoln.yaml'), 'utf8')
    expect(content).toContain('enabled: true')
    expect(content).toContain('workflow_template: interview-to-knowledge')
    expect(content).toContain('min_lincoln_version:')
  })

  it('does not overwrite an existing marker without force', () => {
    const markerPath = path.join(tmpDir, '.lincoln.yaml')
    fs.writeFileSync(markerPath, 'enabled: false\n')
    const code = initProject(tmpDir, { force: false, dryRun: false })
    expect(code).toBe(1)
    expect(fs.readFileSync(markerPath, 'utf8')).toContain('enabled: false')
  })

  it('overwrites an existing marker when force is true', () => {
    const markerPath = path.join(tmpDir, '.lincoln.yaml')
    fs.writeFileSync(markerPath, 'enabled: false\n')
    const code = initProject(tmpDir, { force: true, dryRun: false })
    expect(code).toBe(0)
    expect(fs.readFileSync(markerPath, 'utf8')).toContain('enabled: true')
  })

  it('does not write in dry-run mode', () => {
    const code = initProject(tmpDir, { force: false, dryRun: true })
    expect(code).toBe(0)
    expect(fs.existsSync(path.join(tmpDir, '.lincoln.yaml'))).toBe(false)
  })
})
