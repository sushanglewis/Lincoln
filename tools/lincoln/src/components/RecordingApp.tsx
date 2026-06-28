import { Box, Text } from 'ink'
import React, { useEffect, useState } from 'react'

import { CancelledScreen } from './CancelledScreen'
import { RecordingScreen } from './RecordingScreen'
import { useKeyHandler } from '../hooks/useKeyHandler'

export interface RecordingAppProps {
  sessionId: string
  topic: string
  designId: string
  branch: string
  audioMeterStyle?: 'bar' | 'dot' | 'wave'
}

type RecordingStatus = 'recording' | 'stopped' | 'cancelled'

function mockAmplitude(duration: number): number {
  // Generate a deterministic-looking amplitude between 0.1 and 0.9
  return 0.5 + 0.4 * Math.sin(duration * 0.8)
}

export function RecordingApp({
  sessionId,
  topic,
  designId,
  branch,
  audioMeterStyle = 'bar',
}: RecordingAppProps) {
  const [status, setStatus] = useState<RecordingStatus>('recording')
  const [duration, setDuration] = useState(0)
  const [amplitude, setAmplitude] = useState(0.3)

  useEffect(() => {
    if (status !== 'recording') {
      return
    }

    const interval = setInterval(() => {
      setDuration(d => {
        const next = d + 1
        setAmplitude(mockAmplitude(next))
        return next
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [status])

  useKeyHandler({
    onStop: () => {
      if (status === 'recording') {
        setStatus('stopped')
      }
    },
    onCancel: () => {
      if (status === 'recording') {
        setStatus('cancelled')
      }
    },
  })

  if (status === 'cancelled') {
    return <CancelledScreen />
  }

  if (status === 'stopped') {
    return (
      <Box flexDirection="column" padding={1}>
        <Text bold>Stopped</Text>
        <Text>Recording saved for session {sessionId}.</Text>
      </Box>
    )
  }

  return (
    <RecordingScreen
      sessionId={sessionId}
      topic={topic}
      designId={designId}
      duration={duration}
      amplitude={amplitude}
      audioMeterStyle={audioMeterStyle}
    />
  )
}
