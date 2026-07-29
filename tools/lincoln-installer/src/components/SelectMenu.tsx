import { Box, Text, useInput } from 'ink'
import React, { useState } from 'react'

export interface SelectMenuItem {
  label: string
  value: string
}

export interface SelectMenuProps {
  title?: string
  items: SelectMenuItem[]
  selected: string[]
  multiple?: boolean
  onSelect: (value: string) => void
  onConfirm: (value?: string) => void
  onCancel?: () => void
}

export function SelectMenu({
  title,
  items,
  selected,
  multiple = false,
  onSelect,
  onConfirm,
  onCancel,
}: SelectMenuProps) {
  const [cursor, setCursor] = useState(0)

  useInput((input, key) => {
    if (key.upArrow) {
      setCursor((c) => (c > 0 ? c - 1 : items.length - 1))
    } else if (key.downArrow) {
      setCursor((c) => (c < items.length - 1 ? c + 1 : 0))
    } else if (key.return) {
      if (multiple) {
        onConfirm()
      } else {
        const value = items[cursor]?.value
        if (value) {
          onSelect(value)
          onConfirm(value)
        }
      }
    } else if (key.escape) {
      onCancel?.()
    } else if (input === ' ') {
      const value = items[cursor]?.value
      if (value) {
        onSelect(value)
      }
    }
  })

  return (
    <Box flexDirection="column">
      {title ? <Text bold>{title}</Text> : null}
      {items.map((item, index) => {
        const isCursor = index === cursor
        const isSelected = selected.includes(item.value)
        const marker = multiple ? (isSelected ? '[x]' : '[ ]') : isSelected ? '●' : '○'
        return (
          <Text key={item.value} color={isCursor ? 'cyan' : undefined}>
            {isCursor ? '> ' : '  '}
            {marker} {item.label}
          </Text>
        )
      })}
      <Text dimColor></Text>
      <Text dimColor>{multiple ? 'Space to select, Enter to confirm' : '↑↓ to navigate, Enter to select'}</Text>
    </Box>
  )
}
