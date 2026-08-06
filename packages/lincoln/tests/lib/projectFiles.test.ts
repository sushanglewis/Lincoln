import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { listVendoredFrameworkFiles } from '../../src/lib/projectFiles.js'

describe('listVendoredFrameworkFiles', () => {
  let tmpDir: string

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lincoln-project-files-'))
  })

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true })
  })

  it('lists unmodified files as removable', () => {
    const payload = path.join(tmpDir, 'payload')
    const project = path.join(tmpDir, 'project')
    fs.mkdirSync(path.join(payload, '.claude', 'stages'), { recursive: true })
    fs.mkdirSync(path.join(project, '.claude', 'stages'), { recursive: true })
    fs.writeFileSync(path.join(payload, '.claude', 'stages', 'clarify.yaml'), 'stage: clarify\n')
    fs.writeFileSync(path.join(project, '.claude', 'stages', 'clarify.yaml'), 'stage: clarify\n')

    const report = listVendoredFrameworkFiles(payload, project)
    expect(report.removable).toContain(path.join('.claude', 'stages', 'clarify.yaml'))
    expect(report.modified).toHaveLength(0)
    expect(report.preserved).toHaveLength(0)
  })

  it('lists modified files as modified', () => {
    const payload = path.join(tmpDir, 'payload')
    const project = path.join(tmpDir, 'project')
    fs.mkdirSync(path.join(payload, '.claude', 'agents'), { recursive: true })
    fs.mkdirSync(path.join(project, '.claude', 'agents'), { recursive: true })
    fs.writeFileSync(path.join(payload, '.claude', 'agents', 'default.md'), 'original\n')
    fs.writeFileSync(path.join(project, '.claude', 'agents', 'default.md'), 'changed\n')

    const report = listVendoredFrameworkFiles(payload, project)
    expect(report.modified).toContain(path.join('.claude', 'agents', 'default.md'))
    expect(report.removable).toHaveLength(0)
  })

  it('preserves .context contents', () => {
    const payload = path.join(tmpDir, 'payload')
    const project = path.join(tmpDir, 'project')
    fs.mkdirSync(path.join(project, '.context'), { recursive: true })
    fs.writeFileSync(path.join(project, '.context', 'notes.md'), 'notes\n')

    const report = listVendoredFrameworkFiles(payload, project)
    expect(report.preserved).toContain(path.join('.context', 'notes.md'))
    expect(report.removable).toHaveLength(0)
  })

  it('preserves issue packages', () => {
    const payload = path.join(tmpDir, 'payload')
    const project = path.join(tmpDir, 'project')
    fs.mkdirSync(path.join(project, 'issue-42', 'handoffs'), { recursive: true })
    fs.writeFileSync(path.join(project, 'issue-42', 'handoffs', 'a.md'), 'handoff\n')

    const report = listVendoredFrameworkFiles(payload, project)
    expect(report.preserved).toContain(path.join('issue-42', 'handoffs', 'a.md'))
  })
})
