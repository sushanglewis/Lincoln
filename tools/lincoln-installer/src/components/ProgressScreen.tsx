import { Box, Text } from 'ink'
import React from 'react'

import type { StepResult } from '../hooks/useSetup'

export interface ProgressScreenProps {
  currentStep: string
  results: StepResult[]
}

export function ProgressScreen({ currentStep, results }: ProgressScreenProps) {
  return (
    <Box flexDirection="column" padding={1}>
      <Text bold>Installing Lincoln...</Text>
      {results.map((result) => (
        <Text key={result.step}>
          {result.success ? '✅' : '❌'} {result.step}
        </Text>
      ))}
      {currentStep && !results.some((r) => r.step === currentStep && r.success) && (
        <Text color="cyan">⏳ {currentStep}...</Text>
      )}
    </Box>
  )
}
