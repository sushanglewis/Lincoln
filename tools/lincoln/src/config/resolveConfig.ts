import { homedir } from 'node:os'
import { join } from 'node:path'

import { LincolnConfig, loadConfigOptional } from './loadConfig'
import { generateSessionId } from '../utils/sessionId'

export interface ParsedArgs {
  topic?: string
  designId?: string
  branch?: string
  sessionId?: string
  noTui?: boolean
  help?: boolean
}

export interface ResolvedConfig extends Required<Pick<LincolnConfig, 'autoProcess' | 'showAudioMeter' | 'audioMeterStyle'>> {
  sessionId: string
  topic: string
  designId: string
  branch: string
  noTui: boolean
}

interface ResolveOptions {
  cwd?: string
  home?: string
  now?: Date
}

function pickFirst(...values: Array<string | undefined>): string {
  for (const value of values) {
    if (value !== undefined && value !== '') {
      return value
    }
  }
  return ''
}

export function resolveConfig(args: ParsedArgs, options: ResolveOptions = {}): ResolvedConfig {
  const cwd = options.cwd ?? process.cwd()
  const home = options.home ?? homedir()
  const now = options.now ?? new Date()

  const globalConfig = loadConfigOptional(join(home, '.lincolnrc'))
  const localConfig = loadConfigOptional(join(cwd, '.lincolnrc'))

  const topic = pickFirst(args.topic, localConfig.defaultTopic, globalConfig.defaultTopic)
  const designId = pickFirst(args.designId, localConfig.defaultDesignId, globalConfig.defaultDesignId)
  const branch = pickFirst(args.branch, localConfig.defaultBranch, globalConfig.defaultBranch)

  const descriptor = designId || topic || undefined
  const sessionId = args.sessionId || generateSessionId({ now, descriptor })

  return {
    sessionId,
    topic,
    designId,
    branch,
    noTui: args.noTui ?? false,
    autoProcess: localConfig.autoProcess ?? globalConfig.autoProcess ?? false,
    showAudioMeter: localConfig.showAudioMeter ?? globalConfig.showAudioMeter ?? true,
    audioMeterStyle: localConfig.audioMeterStyle ?? globalConfig.audioMeterStyle ?? 'bar',
  }
}
