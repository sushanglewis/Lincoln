import { Box, Text } from 'ink'
import React, { useState } from 'react'

import type { HarnessInfo } from '../types'
import { SelectMenu } from './SelectMenu'

export interface HarnessSelectScreenProps {
  harnesses: HarnessInfo[]
  selected: string[]
  onConfirm: (selected: string[]) => void
}

export function HarnessSelectScreen({
  harnesses,
  selected: initialSelected,
  onConfirm,
}: HarnessSelectScreenProps) {
  const [selected, setSelected] = useState(initialSelected)
  const items = harnesses.map((h) => ({
    label: `${h.name} ${h.installed ? '(detected)' : ''} - ${h.description}`,
    value: h.id,
  }))

  const handleSelect = (value: string) => {
    setSelected((prev) =>
      prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]
    )
  }

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold>Select agent harnesses</Text>
      <Text dimColor>Choose one or more targets for Lincoln.</Text>
      <SelectMenu
        items={items}
        selected={selected}
        multiple
        onSelect={handleSelect}
        onConfirm={() => onConfirm(selected)}
      />
    </Box>
  )
}
