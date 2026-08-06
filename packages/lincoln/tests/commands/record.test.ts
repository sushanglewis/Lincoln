import { describe, it, expect, vi } from 'vitest'
import { record, makeFakeChildProcess, makeFailingFakeChildProcess } from '../../src/commands/record.js'

describe('record', () => {
  it('delegates to lincoln-record and returns its exit code', async () => {
    const spawn = vi.fn().mockReturnValue(makeFakeChildProcess(0))
    const code = await record(['--help'], { spawn })
    expect(code).toBe(0)
    expect(spawn).toHaveBeenCalledWith('lincoln-record', ['--help'], { stdio: 'inherit' })
  })

  it('returns 1 when lincoln-record cannot be started', async () => {
    const spawn = vi.fn().mockReturnValue(makeFailingFakeChildProcess('ENOENT'))
    const code = await record(['--help'], { spawn })
    expect(code).toBe(1)
  })
})
