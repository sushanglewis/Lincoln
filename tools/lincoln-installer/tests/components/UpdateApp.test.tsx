import { describe, expect, test, vi, afterEach } from 'vitest'
import { render } from 'ink-testing-library'
import { UpdateApp } from '../../src/components/UpdateApp'
import * as updateReleaseModule from '../../src/utils/updateRelease'

async function tick() {
  return new Promise((resolve) => setTimeout(resolve, 0))
}

describe('UpdateApp', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  test('renders welcome and starts checking', async () => {
    vi.spyOn(updateReleaseModule, 'updateRelease').mockResolvedValue({
      success: true,
      fromVersion: '1.2.0',
      toVersion: '1.2.0',
      updated: [],
      preserved: [],
    })

    const { lastFrame } = render(<UpdateApp root="/tmp/proj" repo="sushanglewis/Lincoln" dryRun={false} />)
    await tick()
    expect(lastFrame() ?? '').toMatch(/Lincoln Update|up to date/)
    expect(updateReleaseModule.updateRelease).toHaveBeenCalledWith({
      root: '/tmp/proj',
      repo: 'sushanglewis/Lincoln',
      dryRun: true,
    })
  })

  test('shows up-to-date when versions match', async () => {
    vi.spyOn(updateReleaseModule, 'updateRelease').mockResolvedValue({
      success: true,
      fromVersion: '1.3.0',
      toVersion: '1.3.0',
      updated: [],
      preserved: [],
    })

    const { lastFrame } = render(<UpdateApp root="/tmp/proj" repo="sushanglewis/Lincoln" dryRun={false} />)

    await vi.waitFor(() => expect(lastFrame() ?? '').toContain('up to date'), {
      timeout: 2000,
    })
  })

  test('shows confirm screen when update is available', async () => {
    vi.spyOn(updateReleaseModule, 'updateRelease').mockResolvedValueOnce({
      success: true,
      fromVersion: '1.2.0',
      toVersion: '1.3.0',
      updated: [],
      preserved: [],
    })

    const { lastFrame } = render(<UpdateApp root="/tmp/proj" repo="sushanglewis/Lincoln" dryRun={false} />)

    await vi.waitFor(() => expect(lastFrame() ?? '').toContain('Update available'), {
      timeout: 2000,
    })
  })

  test('starts update on confirm and shows result', async () => {
    const updateSpy = vi
      .spyOn(updateReleaseModule, 'updateRelease')
      .mockResolvedValueOnce({
        success: true,
        fromVersion: '1.2.0',
        toVersion: '1.3.0',
        updated: [],
        preserved: [],
      })
      .mockResolvedValueOnce({
        success: true,
        fromVersion: '1.2.0',
        toVersion: '1.3.0',
        updated: ['README.md'],
        preserved: ['.context'],
      })

    const { lastFrame, stdin } = render(
      <UpdateApp root="/tmp/proj" repo="sushanglewis/Lincoln" dryRun={false} />
    )

    await vi.waitFor(() => expect(lastFrame() ?? '').toContain('Update available'), {
      timeout: 2000,
    })

    stdin.write('\r')
    await tick()

    await vi.waitFor(() => expect(lastFrame() ?? '').toContain('Update complete'), {
      timeout: 2000,
    })

    expect(updateSpy).toHaveBeenCalledTimes(2)
    expect(updateSpy).toHaveBeenLastCalledWith({
      root: '/tmp/proj',
      repo: 'sushanglewis/Lincoln',
      dryRun: false,
    })
  })

  test('displays error when update fails', async () => {
    vi.spyOn(updateReleaseModule, 'updateRelease').mockResolvedValue({
      success: false,
      updated: [],
      preserved: [],
      error: 'network error',
    })

    const { lastFrame } = render(<UpdateApp root="/tmp/proj" repo="sushanglewis/Lincoln" dryRun={false} />)

    await vi.waitFor(() => expect(lastFrame() ?? '').toContain('Update failed'), {
      timeout: 2000,
    })
    expect(lastFrame() ?? '').toContain('network error')
  })

  test('displays error when apply throws after confirmation', async () => {
    const updateSpy = vi
      .spyOn(updateReleaseModule, 'updateRelease')
      .mockResolvedValueOnce({
        success: true,
        fromVersion: '1.2.0',
        toVersion: '1.3.0',
        updated: [],
        preserved: [],
      })
      .mockRejectedValueOnce(new Error('apply failed'))

    const { lastFrame, stdin } = render(
      <UpdateApp root="/tmp/proj" repo="sushanglewis/Lincoln" dryRun={false} />
    )

    await vi.waitFor(() => expect(lastFrame() ?? '').toContain('Update available'), {
      timeout: 2000,
    })

    stdin.write('\r')
    await tick()

    await vi.waitFor(() => expect(lastFrame() ?? '').toContain('Update failed'), {
      timeout: 2000,
    })
    expect(lastFrame() ?? '').toContain('apply failed')
    expect(updateSpy).toHaveBeenCalledTimes(2)
  })

  test('shows dry-run result when dryRun is true', async () => {
    vi.spyOn(updateReleaseModule, 'updateRelease').mockResolvedValue({
      success: true,
      fromVersion: '1.2.0',
      toVersion: '1.3.0',
      updated: [],
      preserved: [],
    })

    const { lastFrame } = render(<UpdateApp root="/tmp/proj" repo="sushanglewis/Lincoln" dryRun />)

    await vi.waitFor(() => expect(lastFrame() ?? '').toContain('Dry run'), {
      timeout: 2000,
    })
    expect(lastFrame() ?? '').toContain('1.2.0 → 1.3.0')
  })

})
