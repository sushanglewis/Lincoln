import { Box, Text } from 'ink'
import React from 'react'

import { AudioMeter } from './AudioMeter'
import { formatDuration } from '../utils/formatDuration'

export interface RecordingScreenProps {
  sessionId: string
  topic: string
  designId: string
  duration: number
  amplitude: number
  audioMeterStyle?: 'bar' | 'dot' | 'wave'
}

export function RecordingScreen({
  sessionId,
  topic,
  designId,
  duration,
  amplitude,
  audioMeterStyle = 'bar',
}: RecordingScreenProps) {
  return (
    <Box flexDirection="column" padding={1}>
      <Text bold>Lincoln Recorder</Text>
      <Text dimColor>Session: {sessionId}</Text>
      {topic ? <Text>Topic: {topic}</Text> : null}
      {designId ? <Text>Design: {designId}</Text> : null}
      <Text />
      <Box>
        <Text color="red">●</Text>
        <Text> Recording {formatDuration(duration)}</Text>
      </Box>
      <Text />
      <AudioMeter amplitude={amplitude} style={audioMeterStyle} />
      <Text />
      <Text dimColor>Press Enter to stop · Press q to cancel</Text>
    </Box>
  )
}
