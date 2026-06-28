import { readFileSync } from 'node:fs'
import { PathLike } from 'node:fs'

import yaml from 'js-yaml'

export interface LincolnConfig {
  defaultTopic?: string
  defaultDesignId?: string
  defaultBranch?: string
  autoProcess?: boolean
  showAudioMeter?: boolean
  audioMeterStyle?: 'bar' | 'dot' | 'wave'
}

function parseConfig(content: string, path: PathLike): LincolnConfig {
  const trimmed = content.trim()
  if (!trimmed) {
    return {}
  }

  const isJson = trimmed.startsWith('{') || trimmed.startsWith('[')
  const raw = isJson ? JSON.parse(trimmed) : yaml.load(trimmed)

  if (raw === null || typeof raw !== 'object') {
    return {}
  }

  const data = raw as Record<string, unknown>

  return {
    defaultTopic: asString(data.default_topic),
    defaultDesignId: asString(data.default_design_id),
    defaultBranch: asString(data.default_branch),
    autoProcess: asBoolean(data.auto_process),
    showAudioMeter: asBoolean(data.show_audio_meter),
    audioMeterStyle: asMeterStyle(data.audio_meter_style),
  }
}

function asString(value: unknown): string | undefined {
  return typeof value === 'string' ? value : undefined
}

function asBoolean(value: unknown): boolean | undefined {
  return typeof value === 'boolean' ? value : undefined
}

function asMeterStyle(value: unknown): LincolnConfig['audioMeterStyle'] {
  if (value === 'bar' || value === 'dot' || value === 'wave') {
    return value
  }
  return undefined
}

export function loadConfig(path: PathLike): LincolnConfig {
  let content: string
  try {
    content = readFileSync(path, 'utf-8')
  } catch (error) {
    throw new Error(`Config file not found: ${String(path)}`)
  }

  try {
    return parseConfig(content, path)
  } catch (error) {
    const cause = error instanceof Error ? error.message : String(error)
    throw new Error(`Failed to parse config ${String(path)}: ${cause}`)
  }
}

export function loadConfigOptional(path: PathLike): LincolnConfig {
  try {
    return loadConfig(path)
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    if (message.includes('Config file not found')) {
      return {}
    }
    throw error
  }
}
