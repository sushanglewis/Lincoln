import { spawn, type ChildProcessByStdio } from 'node:child_process'
import { type Readable, type Writable } from 'node:stream'
import { EventEmitter } from 'node:events'

export interface SpawnRecorderOptions {
  workspaceRoot: string
  sessionId: string
  lincolnRecordPath?: string
  mic?: string | null
  model?: string | null
}

export interface RecorderProcess {
  on(event: 'ready', listener: () => void): this
  on(event: 'error', listener: (error: Error) => void): this
  on(event: 'exit', listener: (code: number | null, signal: NodeJS.Signals | null) => void): this
  stop(): Promise<void>
  cancel(): Promise<void>
}

class RecorderProcessImpl extends EventEmitter implements RecorderProcess {
  private child: ChildProcessByStdio<Writable, Readable, Readable>
  private stopped = false
  private exitPromise: Promise<void>
  private resolveExit: () => void = () => {}
  private exitSettled = false

  constructor(child: ChildProcessByStdio<Writable, Readable, Readable>) {
    super()
    this.child = child
    this.exitPromise = new Promise((resolve) => {
      this.resolveExit = resolve
    })

    this.child.on('error', (error) => {
      this.emit('error', error)
      this.settleExit()
    })

    this.child.on('exit', (code, signal) => {
      this.emit('exit', code, signal)
      this.settleExit()
    })

    this.child.stdout.on('data', (data: Buffer) => {
      process.stdout.write(data)
    })

    this.child.stderr.on('data', (data: Buffer) => {
      process.stderr.write(data)
    })

    // lincoln-record begins capturing immediately; treat it as ready.
    process.nextTick(() => this.emit('ready'))
  }

  private settleExit(): void {
    if (!this.exitSettled) {
      this.exitSettled = true
      this.resolveExit()
    }
  }

  stop(): Promise<void> {
    return this._terminate('SIGINT')
  }

  cancel(): Promise<void> {
    return this._terminate('SIGKILL')
  }

  private _terminate(signal: NodeJS.Signals): Promise<void> {
    if (this.stopped) {
      return this.exitPromise
    }
    this.stopped = true

    if (this.child.killed) {
      return this.exitPromise
    }

    this.child.kill(signal)

    const timeout = setTimeout(() => {
      if (!this.child.killed) {
        this.child.kill('SIGKILL')
      }
    }, 5000)

    this.exitPromise.finally(() => clearTimeout(timeout))

    return this.exitPromise
  }
}

export function spawnRecorder(options: SpawnRecorderOptions): RecorderProcess {
  const {
    workspaceRoot,
    sessionId,
    lincolnRecordPath = 'lincoln-record',
    mic,
    model,
  } = options

  const args: string[] = [
    'record',
    '--session-id',
    sessionId,
    '--output',
    workspaceRoot,
  ]

  if (mic) {
    args.push('--mic', mic)
  }

  if (model) {
    args.push('--model', model)
  }

  const child = spawn(lincolnRecordPath, args, {
    cwd: workspaceRoot,
    stdio: ['pipe', 'pipe', 'pipe'],
  })

  return new RecorderProcessImpl(child)
}
