import { existsSync } from 'node:fs'
import { homedir } from 'node:os'
import { join } from 'node:path'

export const KNOWN_MODELS = [
  'tiny',
  'base',
  'small',
  'medium',
  'large-v1',
  'large-v2',
  'large-v3',
  'large-v3-turbo',
]

export interface ModelStatus {
  name: string
  cached: boolean
}

export function defaultModelCacheDir(): string {
  return join(homedir(), '.cache', 'lincoln', 'models')
}

export function modelCachePath(name: string, cacheDir: string): string {
  return join(cacheDir, 'whisper', `ggml-${name}.bin`)
}

export function listModelStatuses(cacheDir: string): ModelStatus[] {
  return KNOWN_MODELS.map(name => ({
    name,
    cached: existsSync(modelCachePath(name, cacheDir)),
  }))
}
