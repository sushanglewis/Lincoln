import { Box, Text } from 'ink'
import React from 'react'

export interface LogEntry {
  id: string
  message: string
  type?: 'info' | 'success' | 'error' | 'command'
}

export interface LogViewProps {
  logs: LogEntry[]
}

const TYPE_COLORS: Record<string, string | undefined> = {
  info: undefined,
  success: 'green',
  error: 'red',
  command: 'cyan',
}

export function LogView({ logs }: LogViewProps) {
  const visible = logs.slice(-8)

  return (
    <Box flexDirection="column" paddingX={1} flexGrow={1}>
      <Text underline dimColor>Log</Text>
      {visible.length === 0 ? (
        <Text dimColor>No events yet.</Text>
      ) : (
        visible.map(log => (
          <Text key={log.id} color={TYPE_COLORS[log.type ?? 'info']}>{log.message}</Text>
        ))
      )}
    </Box>
  )
}
