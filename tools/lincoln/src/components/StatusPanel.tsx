import { Box, Text } from 'ink'
import React from 'react'

import { formatDuration } from '../utils/formatDuration'

export interface StatusPanelProps {
  sessionId: string
  topic?: string
  designId?: string
  branch?: string
  status: 'idle' | 'recording' | 'stopped' | 'cancelled' | 'error'
  duration: number
  amplitude?: number
}

export function StatusPanel({
  sessionId,
  topic,
  designId,
  branch,
  status,
  duration,
}: StatusPanelProps) {
  const statusLabel = {
    idle: 'Ready',
    recording: `Recording ${formatDuration(duration)}`,
    stopped: 'Stopped',
    cancelled: 'Cancelled',
    error: 'Error',
  }[status]

  const statusColor = status === 'recording' ? 'red' : status === 'error' ? 'red' : status === 'cancelled' ? 'yellow' : 'green'

  return (
    <Box flexDirection="column" paddingX={1} paddingTop={1}>
      <Box flexDirection="row" justifyContent="space-between" alignItems="center">
        <Text bold color="white">Lincoln Recorder</Text>
        <Box flexDirection="row" gap={1}>
          <Text color={statusColor}>{status === 'recording' ? '●' : '○'}</Text>
          <Text>{statusLabel}</Text>
        </Box>
      </Box>

      <Box flexDirection="column" paddingY={1}>
        <Text dimColor>Session: {sessionId}</Text>
        {topic ? <Text dimColor>Topic: {topic}</Text> : null}
        {designId ? <Text dimColor>Design: {designId}</Text> : null}
        {branch ? <Text dimColor>Branch: {branch}</Text> : null}
      </Box>
    </Box>
  )
}
