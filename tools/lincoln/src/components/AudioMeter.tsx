import { Box, Text } from 'ink'
import React from 'react'

import { amplitudeToMeter } from '../utils/amplitudeToMeter'

export interface AudioMeterProps {
  amplitude: number
  style: 'bar' | 'dot' | 'wave'
}

const BLOCKS = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']

export function AudioMeter({ amplitude, style }: AudioMeterProps) {
  const bars = amplitudeToMeter(amplitude, 16)

  if (style === 'bar') {
    const filled = '█'.repeat(bars)
    const empty = '░'.repeat(16 - bars)
    return (<Text>{filled + empty}</Text>)
  }

  if (style === 'dot') {
    const filled = '●'.repeat(bars)
    const empty = '○'.repeat(16 - bars)
    return (<Text>{filled + empty}</Text>)
  }

  // wave
  const wave = BLOCKS.slice(0, Math.max(1, Math.ceil(amplitude * BLOCKS.length)))
    .join('')
    .repeat(2)
    .slice(0, 16)
  return (<Text>{wave.padEnd(16, '~')}</Text>)
}
