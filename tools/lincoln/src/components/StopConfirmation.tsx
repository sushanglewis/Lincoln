import { Box, Text } from 'ink'
import { useInput } from 'ink'
import React from 'react'

export interface StopConfirmationProps {
  sessionId: string
  onConfirm: () => void
  onCancel: () => void
}

export function StopConfirmation({ sessionId, onConfirm, onCancel }: StopConfirmationProps) {
  useInput(input => {
    if (input === 'y') {
      onConfirm()
    } else if (input === 'n') {
      onCancel()
    }
  })

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold>Stopped</Text>
      <Text>Session {sessionId} saved.</Text>
      <Text>Run process-interview to generate knowledge artifacts?</Text>
      <Text>
        <Text color="green">[y]</Text> Yes{' '}
        <Text color="red">[n]</Text> No
      </Text>
    </Box>
  )
}
