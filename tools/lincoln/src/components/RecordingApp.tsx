import { Box, Text, useApp } from 'ink'
import React, { useState } from 'react'

import { CancelledScreen } from './CancelledScreen'
import { RecordingScreen } from './RecordingScreen'
import { ReadyScreen } from './ReadyScreen'
import { StopConfirmation } from './StopConfirmation'
import { useKeyHandler } from '../hooks/useKeyHandler'
import { useRecorder } from '../recording/useRecorder'

export interface RecordingAppProps {
  workspaceRoot: string
  sessionId: string
  topic: string
  designId: string
  branch: string
  audioMeterStyle?: 'bar' | 'dot' | 'wave'
  lincolnRecordPath?: string
}

type AppPhase = 'ready' | 'recording' | 'cancelled'

const MENU_OPTION_COUNT = 2

export function RecordingApp({
  workspaceRoot,
  sessionId,
  topic,
  designId,
  branch,
  audioMeterStyle = 'bar',
  lincolnRecordPath,
}: RecordingAppProps) {
  const { exit } = useApp()
  const [phase, setPhase] = useState<AppPhase>('ready')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const { state, start, stop, cancel } = useRecorder({
    workspaceRoot,
    sessionId,
    lincolnRecordPath,
    startOnMount: false,
  })

  const handleExit = () => {
    exit()
  }

  useKeyHandler({
    onStop: () => {
      if (phase === 'ready') {
        if (selectedIndex === 0) {
          setPhase('recording')
          start()
        } else {
          setPhase('cancelled')
          handleExit()
        }
      } else if (state.status === 'recording') {
        stop().catch(() => {})
      }
    },
    onCancel: async () => {
      if (phase === 'ready') {
        setPhase('cancelled')
      } else if (state.status === 'recording') {
        await cancel().catch(() => {})
      }
      handleExit()
    },
    onUp: () => {
      if (phase === 'ready') {
        setSelectedIndex(index => (index - 1 + MENU_OPTION_COUNT) % MENU_OPTION_COUNT)
      }
    },
    onDown: () => {
      if (phase === 'ready') {
        setSelectedIndex(index => (index + 1) % MENU_OPTION_COUNT)
      }
    },
  })

  if (phase === 'cancelled' || state.status === 'cancelled') {
    return <CancelledScreen />
  }

  if (state.status === 'stopped') {
    return (
      <StopConfirmation
        sessionId={sessionId}
        workspaceRoot={workspaceRoot}
        onConfirm={handleExit}
      />
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

  if (phase === 'ready') {
    return (
      <ReadyScreen
        sessionId={sessionId}
        topic={topic}
        designId={designId}
        branch={branch}
        selectedIndex={selectedIndex}
      />
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
