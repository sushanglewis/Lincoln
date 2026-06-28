import { spawn } from 'node:child_process'

export interface TriggerResult {
  success: boolean
  message: string
}

export function triggerProcessInterview(workspaceRoot: string, sessionId: string): Promise<TriggerResult> {
  return new Promise((resolve, reject) => {
    const child = spawn('claude', ['process-interview', sessionId], {
      cwd: workspaceRoot,
      stdio: 'inherit',
      shell: false,
    })

    child.on('error', error => {
      reject({ success: false, message: `Failed to start process-interview: ${error.message}` })
    })

    child.on('exit', code => {
      if (code === 0) {
        resolve({ success: true, message: 'process-interview completed successfully' })
      } else {
        resolve({ success: false, message: `process-interview exited with code ${code}` })
      }
    })
  })
}
