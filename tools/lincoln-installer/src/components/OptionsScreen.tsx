import { Box, Text, useInput } from 'ink'
import React, { useState } from 'react'

export interface InstallerOptions {
  installRecordingDeps: boolean
  runBenchmark: boolean
}

export interface OptionsScreenProps {
  options: InstallerOptions
  onConfirm: (options: InstallerOptions) => void
}

const OPTIONS: { key: keyof InstallerOptions; label: string }[] = [
  {
    key: 'installRecordingDeps',
    label: 'Install optional recording dependencies (ffmpeg, faster-whisper)',
  },
  { key: 'runBenchmark', label: 'Enable benchmark tooling' },
]

export function OptionsScreen({ options: initialOptions, onConfirm }: OptionsScreenProps) {
  const [cursor, setCursor] = useState(0)
  const [options, setOptions] = useState(initialOptions)

  useInput((input, key) => {
    if (key.upArrow) {
      setCursor((c) => (c > 0 ? c - 1 : OPTIONS.length - 1))
    } else if (key.downArrow) {
      setCursor((c) => (c < OPTIONS.length - 1 ? c + 1 : 0))
    } else if (input === ' ') {
      const key = OPTIONS[cursor].key
      setOptions((o) => ({ ...o, [key]: !o[key] }))
    } else if (key.return) {
      onConfirm(options)
    }
  })

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold>Options</Text>
      {OPTIONS.map((option, index) => {
        const isCursor = index === cursor
        const enabled = options[option.key]
        return (
          <Text key={option.key} color={isCursor ? 'cyan' : undefined}>
            {isCursor ? '> ' : '  '}
            [{enabled ? 'x' : ' '}] {option.label}
          </Text>
        )
      })}
      <Text dimColor></Text>
      <Text dimColor>Space to toggle, Enter to confirm</Text>
    </Box>
  )
}
