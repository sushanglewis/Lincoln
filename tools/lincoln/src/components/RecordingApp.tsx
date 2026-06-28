import { Box, Text } from 'ink'
import React from 'react'

import { CancelledScreen } from './CancelledScreen'
import { RecordingScreen } from './RecordingScreen'
import { useKeyHandler } from '../hooks/useKeyHandler'
import { useRecorder } from '../recording/useRecorder'

export interface RecordingAppProps {
  workspaceRoot: string
  sessionId: string
  topic: string
  designId: string
  branch: string
  audioMeterStyle?: 'bar' | 'dot' | 'wave'
  recordInterviewPath?: string
}

export function RecordingApp({
  workspaceRoot,
  sessionId,
  topic,
  designId,
  branch,
  audioMeterStyle = 'bar',
  recordInterviewPath,
}: RecordingAppProps) {
  const { state, stop, cancel } = useRecorder({
    workspaceRoot,
    sessionId,
    topic,
    designId,
    branch,
    recordInterviewPath,
  })

  useKeyHandler({
    onStop: () => {
      if (state.status === 'recording') {
        stop()
      }
    },
    onCancel: () => {
      if (state.status === 'recording') {
        cancel()
      }
    },
  })

  if (state.status === 'cancelled') {
    return <CancelledScreen />
  }

  if (state.status === 'stopped') {
    return (
      <Box flexDirection="column" padding={1}>
        <Text bold>Stopped</Text>
        <Text>Recording saved for session {sessionId}.</Text>
      </Box>
    )
  }

  if (state.status === 'error') {
    return (
      <Box flexDirection="column" padding={1}>
        <Text bold color="red">Recording error</Text>
        <Text>{state.errorMessage}</Text>
      </Box>
    )
  }

  return (
    <RecordingScreen
      sessionId={sessionId}
      topic={topic}
      designId={designId}
      duration={state.duration}
      amplitude={state.amplitude}
      audioMeterStyle={audioMeterStyle}
    />
  )
}
