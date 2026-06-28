import { EventEmitter } from 'node:events'
import { describe, expect, test, vi, beforeEach, afterEach } from 'vitest'
import { spawnRecorder, type RecorderProcess } from '../../src/recording/spawnRecorder'

describe('spawnRecorder', () => {
  let spawnMock: ReturnType<typeof vi.fn>
  let child: EventEmitter

  beforeEach(() => {
    child = new EventEmitter()
    child.pid = 12345
    child.kill = vi.fn()
    child.stdout = new EventEmitter()
    child.stderr = new EventEmitter()
    spawnMock = vi.fn(() => child)
    vi.doMock('node:child_process', () => ({ spawn: spawnMock }))
  })

  afterEach(() => {
    vi.doUnmock('node:child_process')
  })

  test('spawns record-interview with correct args', async () => {
    const { spawnRecorder: spawnRecorderMocked } = await import('../../src/recording/spawnRecorder')
    spawnRecorderMocked({
      workspaceRoot: '/workspace',
      sessionId: '2026-06-28-test',
      topic: '测试',
      designId: 'checkout-redesign',
      branch: 'main',
      recordInterviewPath: '/usr/local/bin/record-interview',
    })

    expect(spawnMock).toHaveBeenCalledWith(
      '/usr/local/bin/record-interview',
      [
        '2026-06-28-test',
        '--no-confirm',
        '--topic',
        '测试',
        '--design-id',
        'checkout-redesign',
        '--branch',
        'main',
      ],
      expect.objectContaining({ cwd: '/workspace' }),
    )
  })

  test('emits ready when metadata prepared message appears', async () => {
    const { spawnRecorder: spawnRecorderMocked } = await import('../../src/recording/spawnRecorder')
    const recorder = spawnRecorderMocked({
      workspaceRoot: '/workspace',
      sessionId: '2026-06-28-test',
      recordInterviewPath: '/usr/local/bin/record-interview',
    })

    const readyHandler = vi.fn()
    recorder.on('ready', readyHandler)
    child.stdout.emit('data', Buffer.from('Metadata prepared: interviews/2026-06-28-test/metadata.json\n'))

    expect(readyHandler).toHaveBeenCalled()
  })

  test('stop resolves on clean exit', async () => {
    const { spawnRecorder: spawnRecorderMocked } = await import('../../src/recording/spawnRecorder')
    const recorder = spawnRecorderMocked({
      workspaceRoot: '/workspace',
      sessionId: '2026-06-28-test',
      recordInterviewPath: '/usr/local/bin/record-interview',
    })

    const stopPromise = recorder.stop()
    child.emit('exit', 0, null)

    await expect(stopPromise).resolves.toBeUndefined()
  })
})
