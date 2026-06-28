import { Box, Text } from 'ink'
import React from 'react'

export interface ReadyScreenProps {
  sessionId: string
  topic: string
  designId: string
  branch: string
}

export function ReadyScreen({ sessionId, topic, designId, branch }: ReadyScreenProps) {
  return (
    <Box flexDirection="column" borderStyle="round" borderColor="gray" padding={1}>
      <Box flexDirection="row" justifyContent="space-between" alignItems="center">
        <Box gap={1}>
          <Text color="red">●</Text>
          <Text color="yellow">●</Text>
          <Text color="green">●</Text>
        </Box>
        <Text bold color="white">
          Lincoln Recorder
        </Text>
      </Box>

      <Box flexDirection="column" paddingY={1}>
        <Text dimColor>Session: {sessionId}</Text>
        {topic ? <Text dimColor>Topic: {topic}</Text> : null}
        {designId ? <Text dimColor>Design: {designId}</Text> : null}
        {branch ? <Text dimColor>Branch: {branch}</Text> : null}
      </Box>

      <Box flexDirection="column" alignItems="center" paddingY={1}>
        <Text bold color="white">
          Press Enter to start recording
        </Text>
        <Text dimColor>Press q to exit</Text>
      </Box>
    </Box>
  )
}
