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

  test('spawns lincoln-record record with correct args', async () => {
    const { spawnRecorder: spawnRecorderMocked } = await import('../../src/recording/spawnRecorder')
    spawnRecorderMocked({
      workspaceRoot: '/workspace',
      sessionId: '2026-06-28-test',
      lincolnRecordPath: '/usr/local/bin/lincoln-record',
    })

    expect(spawnMock).toHaveBeenCalledWith(
      '/usr/local/bin/lincoln-record',
      [
        'record',
        '--session-id',
        '2026-06-28-test',
        '--output',
        '/workspace',
      ],
      expect.objectContaining({ cwd: '/workspace', stdio: ['pipe', 'pipe', 'pipe'] }),
    )
  })

  test('emits ready immediately after spawn', async () => {
    const { spawnRecorder: spawnRecorderMocked } = await import('../../src/recording/spawnRecorder')
    const recorder = spawnRecorderMocked({
      workspaceRoot: '/workspace',
      sessionId: '2026-06-28-test',
    })

    const readyHandler = vi.fn()
    recorder.on('ready', readyHandler)

    await new Promise((resolve) => setImmediate(resolve))
    expect(readyHandler).toHaveBeenCalled()
  })

  test('stop sends SIGINT and resolves on exit', async () => {
    const { spawnRecorder: spawnRecorderMocked } = await import('../../src/recording/spawnRecorder')
    const recorder = spawnRecorderMocked({
      workspaceRoot: '/workspace',
      sessionId: '2026-06-28-test',
    })

    const stopPromise = recorder.stop()
    expect(child.kill).toHaveBeenCalledWith('SIGINT')
    child.emit('exit', 0, null)

    await expect(stopPromise).resolves.toBeUndefined()
  })

  test('cancel sends SIGKILL and resolves on exit', async () => {
    const { spawnRecorder: spawnRecorderMocked } = await import('../../src/recording/spawnRecorder')
    const recorder = spawnRecorderMocked({
      workspaceRoot: '/workspace',
      sessionId: '2026-06-28-test',
    })

    const cancelPromise = recorder.cancel()
    expect(child.kill).toHaveBeenCalledWith('SIGKILL')
    child.emit('exit', null, 'SIGTERM')

    await expect(cancelPromise).resolves.toBeUndefined()
  })
})
