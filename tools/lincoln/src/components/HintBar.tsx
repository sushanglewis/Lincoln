import { Box, Text } from 'ink'
import React from 'react'

export type HintKey = 'idle' | 'recording' | 'stopped' | 'cancelled' | 'error' | 'menu'

export interface HintBarProps {
  mode: HintKey
}

const HINTS: Record<HintKey, string> = {
  idle: '[r] record  [d] devices  [m] model  [q] quit',
  recording: '[s] stop  [c] cancel',
  stopped: '[any key] exit',
  cancelled: '[q] exit',
  error: '[q] exit',
  menu: '[↑↓] select  [enter] confirm  [esc] back',
}

export function HintBar({ mode }: HintBarProps) {
  return (
    <Box paddingX={1} paddingY={1}>
      <Text dimColor>{HINTS[mode]}</Text>
    </Box>
  )
}
