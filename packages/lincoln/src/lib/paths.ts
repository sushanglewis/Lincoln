import path from 'node:path'
import os from 'node:os'

export interface LincolnPaths {
  homeDir: string
  lincolnHome: string
  versionsDir: string
  currentDir: string
  versionMarker: string
  venvDir: string
  claudeDir: string
  codexDir: string
  opencodeDir: string
}

export function resolveLincolnPaths(overrideHomeDir?: string): LincolnPaths {
  const homeDir = overrideHomeDir ?? os.homedir()
  const lincolnHome = process.env.LINCOLN_HOME
    ? path.resolve(process.env.LINCOLN_HOME)
    : path.join(homeDir, '.lincoln')

  return {
    homeDir,
    lincolnHome,
    versionsDir: path.join(lincolnHome, 'versions'),
    currentDir: path.join(lincolnHome, 'current'),
    versionMarker: path.join(lincolnHome, 'marker.json'),
    venvDir: path.join(lincolnHome, 'venv'),
    claudeDir: path.join(homeDir, '.claude'),
    codexDir: path.join(homeDir, '.codex'),
    opencodeDir: path.join(homeDir, '.opencode')
  }
}
