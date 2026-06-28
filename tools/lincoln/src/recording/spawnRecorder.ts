import { spawn, type ChildProcessByStdio } from 'node:child_process'
import { type Readable } from 'node:stream'
import { EventEmitter } from 'node:events'

export interface SpawnRecorderOptions {
  workspaceRoot: string
  sessionId: string
  topic?: string
  designId?: string
  branch?: string
  recordInterviewPath?: string
}

export interface RecorderProcess {
  on(event: 'ready' | 'error' | 'exit', listener: (...args: any[]) => void): this
  stop(): Promise<void>
  cancel(): Promise<void>
}

class RecorderProcessImpl extends EventEmitter implements RecorderProcess {
  private child: ChildProcessByStdio<null, Readable, Readable>
  private stopped = false
  private exitPromise: Promise<void>
  private resolveExit: () => void = () => {}
  private rejectExit: (reason: Error) => void = () => {}

  constructor(child: ChildProcessByStdio<null, Readable, Readable>) {
    super()
    this.child = child
    this.exitPromise = new Promise((resolve, reject) => {
      this.resolveExit = resolve
      this.rejectExit = reject
    })

    this.child.on('error', error => {
      if (!this.stopped) {
        this.emit('error', error)
        this.rejectExit(error)
      }
    })

    this.child.on('exit', (code, signal) => {
      this.emit('exit', code, signal)
      if (code !== 0 && code !== null && !this.stopped) {
        this.rejectExit(new Error(`record-interview exited with code ${code}`))
      } else {
        this.resolveExit()
      }
    })

    this.child.stdout.on('data', (data: Buffer) => {
      const line = data.toString('utf-8')
      if (line.includes('Metadata prepared')) {
        this.emit('ready')
      }
    })

    this.child.stderr.on('data', (data: Buffer) => {
      // Forward stderr for debugging; could be parsed for levels in future
      process.stderr.write(data)
    })
  }

  stop(): Promise<void> {
    return this._terminate(false)
  }

  cancel(): Promise<void> {
    return this._terminate(true)
  }

  private _terminate(force: boolean): Promise<void> {
    if (this.stopped) {
      return this.exitPromise
    }
    this.stopped = true

    if (this.child.killed) {
      return this.exitPromise
    }

    this.child.kill(force ? 'SIGKILL' : 'SIGINT')

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
    topic,
    designId,
    branch,
    recordInterviewPath = 'record-interview',
  } = options

  const args: string[] = [sessionId, '--no-confirm']
  if (topic) args.push('--topic', topic)
  if (designId) args.push('--design-id', designId)
  if (branch) args.push('--branch', branch)

  const child = spawn(recordInterviewPath, args, {
    cwd: workspaceRoot,
    stdio: ['ignore', 'pipe', 'pipe'],
  })

  return new RecorderProcessImpl(child)
}
