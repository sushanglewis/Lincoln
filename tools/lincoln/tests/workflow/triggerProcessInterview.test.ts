import { EventEmitter } from 'node:events'
import type { ChildProcess } from 'node:child_process'
import { describe, expect, test, vi } from 'vitest'

describe('triggerProcessInterview', () => {
  test('spawns claude process-interview with session id', async () => {
    const spawnMock = vi.fn(() => {
      const child = new EventEmitter() as unknown as ChildProcess
      child.pid = 12345
      child.kill = vi.fn()
      process.nextTick(() => child.emit('exit', 0, null))
      return child
    })

    vi.doMock('node:child_process', () => ({ spawn: spawnMock }))
    const { triggerProcessInterview } = await import('../../src/workflow/triggerProcessInterview')

    await triggerProcessInterview('/workspace', '2026-06-28-test')

    expect(spawnMock).toHaveBeenCalledWith(
      'claude',
      ['process-interview', '2026-06-28-test'],
      expect.objectContaining({ cwd: '/workspace' }),
    )

    vi.doUnmock('node:child_process')
  })
})
