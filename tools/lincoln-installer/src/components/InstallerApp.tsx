import { Box, Text } from 'ink'
import React, { useState, useEffect } from 'react'

import type { InstallerConfig } from '../config/resolveConfig'
import type { HarnessInfo } from '../types'
import { detectHarnesses } from '../utils/detectHarness'
import { useSetup, type SetupPhase } from '../hooks/useSetup'
import { HarnessSelectScreen } from './HarnessSelectScreen'
import { OptionsScreen, type InstallerOptions } from './OptionsScreen'
import { ProgressScreen } from './ProgressScreen'
import { ResultScreen } from './ResultScreen'
import { SummaryScreen } from './SummaryScreen'
import { WelcomeScreen } from './WelcomeScreen'

export interface InstallerAppProps {
  config: InstallerConfig
}

export function InstallerApp({ config }: InstallerAppProps) {
  const [phase, setPhase] = useState<SetupPhase>('welcome')
  const [harnesses, setHarnesses] = useState<HarnessInfo[]>([])
  const [selectedHarnesses, setSelectedHarnesses] = useState<string[]>([])
  const [options, setOptions] = useState<InstallerOptions>({
    installRecordingDeps: false,
    runBenchmark: false,
  })

  const { isRunning, results, currentStep, error, startSetup } = useSetup()

  useEffect(() => {
    const detected = detectHarnesses(config.root)
    setHarnesses(detected)
    setSelectedHarnesses(detected.filter((h) => h.installed).map((h) => h.id))
  }, [config.root])

  useEffect(() => {
    if (!isRunning && phase === 'running') {
      setPhase('result')
    }
  }, [isRunning, phase])

  const handleHarnessConfirm = (selected: string[]) => {
    setSelectedHarnesses(selected)
    setPhase('options')
  }

  const handleOptionsConfirm = (opts: InstallerOptions) => {
    setOptions(opts)
    setPhase('summary')
  }

  const handleSummaryConfirm = () => {
    startSetup({
      root: config.root,
      harnesses: selectedHarnesses,
      yes: config.yes,
      dryRun: config.dryRun,
    })
    setPhase('running')
  }

  const handleCancel = () => {
    process.exit(0)
  }

  switch (phase) {
    case 'welcome':
      return <WelcomeScreen onStart={() => setPhase('harness')} />
    case 'harness':
      return (
        <HarnessSelectScreen
          harnesses={harnesses}
          selected={selectedHarnesses}
          onConfirm={handleHarnessConfirm}
        />
      )
    case 'options':
      return <OptionsScreen options={options} onConfirm={handleOptionsConfirm} />
    case 'summary':
      return (
        <SummaryScreen
          root={config.root}
          selectedHarnesses={selectedHarnesses}
          harnesses={harnesses}
          options={options}
          dryRun={config.dryRun}
          onConfirm={handleSummaryConfirm}
          onCancel={handleCancel}
        />
      )
    case 'running':
      return <ProgressScreen currentStep={currentStep} results={results} />
    case 'result':
      return <ResultScreen results={results} error={error} onFinish={() => process.exit(0)} />
    default:
      return <Text>Unknown phase</Text>
  }
}
