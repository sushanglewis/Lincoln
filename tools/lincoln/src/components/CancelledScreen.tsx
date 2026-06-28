import { Box, Text } from 'ink'
import React from 'react'

export function CancelledScreen() {
  return (
    <Box flexDirection="column" padding={1}>
      <Text bold color="yellow">Recording cancelled</Text>
      <Text>No files were saved.</Text>
    </Box>
  )
}
