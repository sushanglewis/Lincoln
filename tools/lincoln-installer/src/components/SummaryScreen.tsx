import { Box, Text, useInput } from 'ink'
import React from 'react'

import type { HarnessInfo } from '../types'

export interface SummaryScreenProps {
  root: string
  selectedHarnesses: string[]
  harnesses: HarnessInfo[]
  options: { installRecordingDeps: boolean; runBenchmark: boolean }
  dryRun: boolean
  onConfirm: () => void
  onCancel: () => void
}

export function SummaryScreen({
  root,
  selectedHarnesses,
  harnesses,
  options,
  dryRun,
  onConfirm,
  onCancel,
}: SummaryScreenProps) {
  useInput((_, key) => {
    if (key.return) {
      onConfirm()
    } else if (key.escape) {
      onCancel()
    }
  })

  const harnessNames = selectedHarnesses
    .map((id) => harnesses.find((h) => h.id === id)?.name || id)
    .join(', ')

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold>Summary</Text>
      <Text>Project root: {root}</Text>
      <Text>Harnesses: {harnessNames}</Text>
      <Text>Recording deps: {options.installRecordingDeps ? 'yes' : 'no'}</Text>
      <Text>Benchmark: {options.runBenchmark ? 'yes' : 'no'}</Text>
      {dryRun && <Text color="yellow">Dry-run mode: no changes will be made.</Text>}
      <Text dimColor></Text>
      <Text>Press Enter to proceed or Esc to cancel.</Text>
    </Box>
  )
}
