import { describe, expect, test, vi, afterEach } from 'vitest'
import * as updateReleaseModule from '../src/utils/updateRelease'

vi.mock('ink', async (importOriginal) => {
  const actual = await importOriginal<typeof import('ink')>()
  return {
    ...actual,
    render: vi.fn(),
  }
})

describe('updateMain', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  test('prints help and exits zero for --help', async () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { render: mockedRender } = await import('ink')
    const { updateMain } = await import('../src/update')
    await updateMain(['--help'])
    expect(errorSpy).not.toHaveBeenCalled()
    expect(process.exitCode).not.toBe(1)
    expect(mockedRender).toHaveBeenCalled()
    const element = (mockedRender as unknown as ReturnType<typeof vi.fn>).mock.calls[0][0]
    expect(element.props.args.help).toBe(true)
  })

  test('prints JSON result for --no-tui --format json', async () => {
    vi.spyOn(updateReleaseModule, 'updateRelease').mockResolvedValue({
      success: true,
      fromVersion: '1.2.0',
      toVersion: '1.3.0',
      updated: ['README.md'],
      preserved: ['.context'],
    })
    const logSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

    const { updateMain } = await import('../src/update')
    await updateMain(['--root', '/tmp/proj', '--no-tui', '--format', 'json'])

    expect(logSpy).toHaveBeenCalled()
    const output = JSON.parse(logSpy.mock.calls[0][0] as string)
    expect(output.success).toBe(true)
    expect(output.toVersion).toBe('1.3.0')
  })

  test('prints human result for --no-tui --format human', async () => {
    vi.spyOn(updateReleaseModule, 'updateRelease').mockResolvedValue({
      success: true,
      fromVersion: '1.2.0',
      toVersion: '1.3.0',
      updated: ['README.md'],
      preserved: ['.context'],
      backupDir: '/tmp/.context/lincoln-update-backup',
    })
    const logSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

    const { updateMain } = await import('../src/update')
    await updateMain(['--root', '/tmp/proj', '--no-tui', '--format', 'human'])

    expect(logSpy).toHaveBeenCalled()
    const output = logSpy.mock.calls.map((call) => call[0]).join('\n')
    expect(output).toContain('Update available')
    expect(output).toContain('README.md')
    expect(output).toContain('Preserved user data')
  })

  test('prints error for invalid argument', async () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { updateMain } = await import('../src/update')
    await updateMain(['--unknown'])
    expect(errorSpy).toHaveBeenCalled()
  })

  test('rejects invalid repository slug', async () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { updateMain } = await import('../src/update')
    await updateMain(['--repo', 'invalid'])
    expect(errorSpy).toHaveBeenCalled()
    expect(process.exitCode).toBe(1)
  })

  test('renders TUI by default', async () => {
    const { render: mockedRender } = await import('ink')
    const { updateMain } = await import('../src/update')
    await updateMain(['--root', '/tmp/proj'])
    expect(mockedRender).toHaveBeenCalled()
    const element = (mockedRender as unknown as ReturnType<typeof vi.fn>).mock.calls[0][0]
    expect(element.props.args.noTui).toBe(false)
  })

  test('prints human result for failed update', async () => {
    vi.spyOn(updateReleaseModule, 'updateRelease').mockResolvedValue({
      success: false,
      updated: [],
      preserved: [],
      error: 'network error',
    })
    const logSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

    const { updateMain } = await import('../src/update')
    await updateMain(['--root', '/tmp/proj', '--no-tui', '--format', 'human'])

    expect(logSpy).toHaveBeenCalled()
    expect(logSpy.mock.calls[0][0]).toContain('network error')
  })
})
