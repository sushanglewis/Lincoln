import React from 'react'
import { describe, expect, test, vi } from 'vitest'
import { render } from 'ink-testing-library'
import { WelcomeScreen } from '../../src/components/WelcomeScreen'
import { HarnessSelectScreen } from '../../src/components/HarnessSelectScreen'
import { OptionsScreen } from '../../src/components/OptionsScreen'
import { SummaryScreen } from '../../src/components/SummaryScreen'
import { ProgressScreen } from '../../src/components/ProgressScreen'
import { ResultScreen } from '../../src/components/ResultScreen'
import { SelectMenu } from '../../src/components/SelectMenu'
import type { HarnessInfo } from '../../src/types'

async function tick() {
  return new Promise((resolve) => setTimeout(resolve, 0))
}

describe('WelcomeScreen', () => {
  test('renders welcome message', () => {
    const { lastFrame } = render(<WelcomeScreen onStart={() => {}} />)
    expect(lastFrame()).toContain('Welcome to Lincoln')
  })

  test('calls onStart on enter', async () => {
    const onStart = vi.fn()
    const { stdin } = render(<WelcomeScreen onStart={onStart} />)
    await tick()
    stdin.write('\r')
    await tick()
    expect(onStart).toHaveBeenCalled()
  })

  test('ignores non-enter keys', async () => {
    const onStart = vi.fn()
    const { stdin } = render(<WelcomeScreen onStart={onStart} />)
    await tick()
    stdin.write('x')
    await tick()
    expect(onStart).not.toHaveBeenCalled()
  })
})

describe('SelectMenu', () => {
  test('selects item with enter in single mode', async () => {
    const onSelect = vi.fn()
    const onConfirm = vi.fn()
    const { stdin } = render(
      <SelectMenu
        title="Choose"
        items={[
          { label: 'One', value: 'one' },
          { label: 'Two', value: 'two' },
        ]}
        selected={[]}
        onSelect={onSelect}
        onConfirm={onConfirm}
      />
    )
    await tick()
    stdin.write('\r')
    await tick()
    expect(onSelect).toHaveBeenCalledWith('one')
    expect(onConfirm).toHaveBeenCalledWith('one')
  })

  test('toggles item with space in multiple mode', async () => {
    const onSelect = vi.fn()
    const { stdin } = render(
      <SelectMenu
        title="Choose"
        items={[
          { label: 'One', value: 'one' },
          { label: 'Two', value: 'two' },
        ]}
        selected={[]}
        multiple
        onSelect={onSelect}
        onConfirm={() => {}}
      />
    )
    await tick()
    stdin.write(' ')
    await tick()
    expect(onSelect).toHaveBeenCalledWith('one')
  })

  test('navigates down and selects second item', async () => {
    const onSelect = vi.fn()
    const onConfirm = vi.fn()
    const { stdin } = render(
      <SelectMenu
        title="Choose"
        items={[
          { label: 'One', value: 'one' },
          { label: 'Two', value: 'two' },
        ]}
        selected={[]}
        onSelect={onSelect}
        onConfirm={onConfirm}
      />
    )
    await tick()
    stdin.write('\x1b[B')
    await tick()
    stdin.write('\r')
    await tick()
    expect(onSelect).toHaveBeenCalledWith('two')
    expect(onConfirm).toHaveBeenCalledWith('two')
  })
})

describe('HarnessSelectScreen', () => {
  const harnesses: HarnessInfo[] = [
    { id: 'claude-code', name: 'Claude Code', description: 'Anthropic', installed: false },
    { id: 'codex', name: 'Codex', description: 'OpenAI', installed: true },
  ]

  test('renders harness options and confirms selection', async () => {
    const onConfirm = vi.fn()
    const { lastFrame, stdin } = render(
      <HarnessSelectScreen
        harnesses={harnesses}
        selected={['codex']}
        onConfirm={onConfirm}
      />
    )
    await tick()
    expect(lastFrame()).toContain('Claude Code')
    expect(lastFrame()).toContain('Codex')
    stdin.write(' ')
    await tick()
    stdin.write('\r')
    await tick()
    expect(onConfirm).toHaveBeenCalledWith(expect.arrayContaining(['codex', 'claude-code']))
  })
})

describe('OptionsScreen', () => {
  test('toggles option with space and confirms', async () => {
    const onConfirm = vi.fn()
    const { stdin } = render(
      <OptionsScreen
        options={{ installRecordingDeps: false, runBenchmark: false }}
        onConfirm={onConfirm}
      />
    )
    await tick()
    stdin.write(' ')
    await tick()
    stdin.write('\r')
    await tick()
    expect(onConfirm).toHaveBeenCalledWith({
      installRecordingDeps: true,
      runBenchmark: false,
    })
  })

  test('wraps cursor with up and down arrows', async () => {
    const { lastFrame, stdin } = render(
      <OptionsScreen
        options={{ installRecordingDeps: false, runBenchmark: false }}
        onConfirm={() => {}}
      />
    )
    await tick()
    stdin.write('\x1b[A')
    await tick()
    expect(lastFrame()).toContain('Enable benchmark tooling')
    stdin.write('\x1b[B')
    await tick()
    stdin.write('\x1b[B')
    await tick()
    expect(lastFrame()).toContain('Enable benchmark tooling')
  })
})

describe('SummaryScreen', () => {
  test('renders summary and confirms', async () => {
    const onConfirm = vi.fn()
    const onCancel = vi.fn()
    const { lastFrame, stdin } = render(
      <SummaryScreen
        root="/tmp/proj"
        selectedHarnesses={['claude-code']}
        harnesses={[
          { id: 'claude-code', name: 'Claude Code', description: '', installed: false },
        ]}
        options={{ installRecordingDeps: false, runBenchmark: true }}
        dryRun={false}
        onConfirm={onConfirm}
        onCancel={onCancel}
      />
    )
    await tick()
    expect(lastFrame()).toContain('/tmp/proj')
    expect(lastFrame()).toContain('Claude Code')
    stdin.write('\r')
    await tick()
    expect(onConfirm).toHaveBeenCalled()
  })

  test('cancels on escape', async () => {
    const onCancel = vi.fn()
    const { stdin } = render(
      <SummaryScreen
        root="/tmp/proj"
        selectedHarnesses={[]}
        harnesses={[]}
        options={{ installRecordingDeps: false, runBenchmark: false }}
        dryRun={true}
        onConfirm={() => {}}
        onCancel={onCancel}
      />
    )
    await tick()
    stdin.write('\x1b')
    await tick()
    expect(onCancel).toHaveBeenCalled()
  })
})

describe('ProgressScreen', () => {
  test('renders completed and current steps', () => {
    const { lastFrame } = render(
      <ProgressScreen
        currentStep="install-clis"
        results={[
          { step: 'check', success: true },
          { step: 'install-skills', success: true },
        ]}
      />
    )
    expect(lastFrame()).toContain('check')
    expect(lastFrame()).toContain('install-clis')
  })
})

describe('ResultScreen', () => {
  test('renders success when all steps pass', () => {
    const { lastFrame } = render(
      <ResultScreen
        results={[{ step: 'check', success: true }]}
        onFinish={() => {}}
      />
    )
    expect(lastFrame()).toContain('complete')
  })

  test('renders failure for failed step', () => {
    const { lastFrame } = render(
      <ResultScreen
        results={[{ step: 'check', success: false, error: 'oops' }]}
        onFinish={() => {}}
      />
    )
    expect(lastFrame()).toContain('incomplete')
    expect(lastFrame()).toContain('oops')
  })
})

describe('SelectMenu extras', () => {
  test('calls onCancel on escape', async () => {
    const onCancel = vi.fn()
    const { stdin } = render(
      <SelectMenu
        title="Choose"
        items={[{ label: 'One', value: 'one' }]}
        selected={[]}
        onSelect={() => {}}
        onConfirm={() => {}}
        onCancel={onCancel}
      />
    )
    await tick()
    stdin.write('\x1b')
    await tick()
    expect(onCancel).toHaveBeenCalled()
  })

  test('navigates up and wraps cursor', async () => {
    const { lastFrame, stdin } = render(
      <SelectMenu
        title="Choose"
        items={[
          { label: 'One', value: 'one' },
          { label: 'Two', value: 'two' },
        ]}
        selected={[]}
        onSelect={() => {}}
        onConfirm={() => {}}
      />
    )
    await tick()
    stdin.write('\x1b[A')
    await tick()
    expect(lastFrame()).toContain('> ○ Two')
  })
})

describe('ResultScreen extras', () => {
  test('calls onFinish on enter', async () => {
    const onFinish = vi.fn()
    const { stdin } = render(
      <ResultScreen results={[{ step: 'check', success: true }]} onFinish={onFinish} />
    )
    await tick()
    stdin.write('\r')
    await tick()
    expect(onFinish).toHaveBeenCalled()
  })
})
