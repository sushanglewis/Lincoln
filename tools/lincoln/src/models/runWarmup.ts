import { spawn } from 'node:child_process'

import { parseWarmupProgress, type WarmupProgress } from './warmupProgress'

export interface RunWarmupOptions {
  model: string
  lincolnRecordPath?: string
  onProgress?: (progress: WarmupProgress) => void
}

const READY_LINE = /Model ready at (.+)/

export function runWarmup(options: RunWarmupOptions): Promise<string> {
  const { model, lincolnRecordPath = 'lincoln-record', onProgress } = options

  return new Promise((resolve, reject) => {
    const child = spawn(lincolnRecordPath, ['warmup', '--model', model], {
      stdio: ['ignore', 'pipe', 'pipe'],
    })

    let readyPath: string | null = null

    child.stdout.on('data', (data: Buffer) => {
      const match = READY_LINE.exec(data.toString())
      if (match) {
        readyPath = match[1].trim()
      }
    })

    child.stderr.on('data', (data: Buffer) => {
      const progress = parseWarmupProgress(data.toString())
      if (progress) {
        onProgress?.(progress)
      }
    })

    child.on('error', reject)
    child.on('exit', code => {
      if (code === 0) {
        resolve(readyPath ?? model)
      } else {
        reject(new Error(`lincoln-record warmup exited with code ${code}`))
      }
    })
  })
}
