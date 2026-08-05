export interface SyncedFile {
  path: string
  sha256: string
}

export interface SyncManifest {
  version: string
  files: SyncedFile[]
  settingsTouched: string[]
}

export function createSyncManifest(
  version: string,
  files: SyncedFile[],
  settingsTouched: string[] = []
): SyncManifest {
  return {
    version,
    files: files.slice().sort((a, b) => a.path.localeCompare(b.path)),
    settingsTouched: settingsTouched.slice().sort()
  }
}

export function findFileByPath(
  manifest: SyncManifest,
  filePath: string
): SyncedFile | undefined {
  return manifest.files.find((f) => f.path === filePath)
}
