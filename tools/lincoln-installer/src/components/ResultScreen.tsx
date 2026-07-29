import { Box, Text, useInput } from 'ink'
import React from 'react'

import type { StepResult } from '../hooks/useSetup'

export interface ResultScreenProps {
  results: StepResult[]
  error?: string
  onFinish: () => void
}

export function ResultScreen({ results, error, onFinish }: ResultScreenProps) {
  useInput((_, key) => {
    if (key.return || key.escape) {
      onFinish()
    }
  })

  const allSuccess = results.length > 0 && results.every((r) => r.success)

  return (
    <Box flexDirection="column" padding={1}>
      {allSuccess ? (
        <Text bold color="green">✅ Lincoln installation complete!</Text>
      ) : (
        <Text bold color="red">❌ Installation incomplete</Text>
      )}
      {error && <Text color="red">{error}</Text>}
      {results.map((result) => (
        <Box key={result.step} flexDirection="column" marginBottom={1}>
          <Text>
            {result.success ? '✅' : '❌'} {result.step}
          </Text>
          {result.error && <Text color="red">  {result.error}</Text>}
        </Box>
      ))}
      <Text dimColor>Press Enter or Esc to exit.</Text>
    </Box>
  )
}
