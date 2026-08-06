import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'

export type HarnessId = 'claude-code' | 'codex' | 'opencode'

export interface GlobalHarnessInfo {
  id: HarnessId
  installed: boolean
  configDir: string
  pluginManaged: boolean
}

interface HarnessSpec {
  id: HarnessId
  configDirName: string
  pluginMarker?: string
}

const HARNESS_SPECS: HarnessSpec[] = [
  {
    id: 'claude-code',
    configDirName: '.claude',
    pluginMarker: 'plugins/lincoln'
  },
  { id: 'codex', configDirName: '.codex' },
  { id: 'opencode', configDirName: '.opencode' }
]

export function detectGlobalHarnesses(
  overrideHomeDir?: string
): GlobalHarnessInfo[] {
  const homeDir = overrideHomeDir ?? os.homedir()

  return HARNESS_SPECS.map((spec) => {
    const configDir = path.join(homeDir, spec.configDirName)
    const installed = fs.existsSync(configDir)
    const pluginManaged = spec.pluginMarker
      ? fs.existsSync(path.join(configDir, spec.pluginMarker))
      : false

    return {
      id: spec.id,
      installed,
      configDir,
      pluginManaged
    }
  })
}

export function installedHarnessIds(homeDir?: string): HarnessId[] {
  return detectGlobalHarnesses(homeDir)
    .filter((h) => h.installed)
    .map((h) => h.id)
}
