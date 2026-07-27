import { spawn } from 'node:child_process'

export interface RunSetupOptions {
  root: string
  command: string
  args: string[]
}

export interface RunSetupResult {
  success: boolean
  code: number | null
  stdout: string
  stderr: string
  error?: string
}

export function runSetup(options: RunSetupOptions): Promise<RunSetupResult> {
  return new Promise((resolve) => {
    const { root, command, args } = options
    const proc = spawn(command, args, {
      cwd: root,
      stdio: ['ignore', 'pipe', 'pipe'],
    })

    let stdout = ''
    let stderr = ''
    let settled = false

    function finish(result: RunSetupResult): void {
      if (settled) return
      settled = true
      resolve(result)
    }

    proc.stdout.on('data', (data: Buffer) => {
      stdout += data.toString('utf-8')
    })

    proc.stderr.on('data', (data: Buffer) => {
      stderr += data.toString('utf-8')
    })

    proc.on('error', (error) => {
      finish({ success: false, code: null, stdout, stderr, error: error.message })
    })

    proc.on('close', (code) => {
      finish({ success: code === 0, code, stdout, stderr })
    })
  })
}

export function parseJsonOutput(stdout: string): unknown {
  const lines = stdout.trim().split('\n')
  const lastLine = lines[lines.length - 1]
  if (!lastLine) return undefined
  try {
    return JSON.parse(lastLine)
  } catch {
    return undefined
  }
}
