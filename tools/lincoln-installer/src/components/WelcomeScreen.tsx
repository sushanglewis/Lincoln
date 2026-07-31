import { Box, Text, useInput } from 'ink'
import React from 'react'

export interface WelcomeScreenProps {
  onStart: () => void
}

export function WelcomeScreen({ onStart }: WelcomeScreenProps) {
  useInput((_, key) => {
    if (key.return) {
      onStart()
    }
  })

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold color="cyan">Welcome to Lincoln</Text>
      <Text>This installer will set up Lincoln in your project.</Text>
      <Text dimColor>Press Enter to start.</Text>
    </Box>
  )
}
