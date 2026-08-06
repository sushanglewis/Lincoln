import { spawn, type ChildProcess } from 'node:child_process'
import { EventEmitter } from 'node:events'

export interface RecordDeps {
  spawn: (
    command: string,
    args: readonly string[],
    options: { stdio: 'inherit' }
  ) => ChildProcess
}

export function createDefaultDeps(): RecordDeps {
  return { spawn }
}

export function record(args: string[], deps: RecordDeps = createDefaultDeps()): Promise<number> {
  return new Promise((resolve) => {
    const child = deps.spawn('lincoln-record', args, { stdio: 'inherit' })
    child.on('error', (err: Error) => {
      console.error(`Failed to start lincoln-record: ${err.message}`)
      resolve(1)
    })
    child.on('close', (code: number | null) => {
      resolve(code ?? 0)
    })
  })
}

export function makeFakeChildProcess(exitCode: number | null = 0): ChildProcess {
  const emitter = new EventEmitter() as ChildProcess
  process.nextTick(() => {
    emitter.emit('close', exitCode)
  })
  return emitter
}

export function makeFailingFakeChildProcess(message: string): ChildProcess {
  const emitter = new EventEmitter() as ChildProcess
  process.nextTick(() => {
    emitter.emit('error', new Error(message))
  })
  return emitter
}
