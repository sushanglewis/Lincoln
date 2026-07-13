import { Box, Text, useInput } from 'ink'
import React, { useState } from 'react'

export interface SelectMenuItem {
  key: string
  label: string
}

export interface SelectMenuProps {
  title: string
  items: SelectMenuItem[]
  onSelect: (key: string) => void
  onClose: () => void
  footer?: string
}

export function SelectMenu({ title, items, onSelect, onClose, footer }: SelectMenuProps) {
  const [index, setIndex] = useState(0)

  useInput((_input, key) => {
    if (key.escape) {
      onClose()
      return
    }
    if (key.upArrow) {
      setIndex(i => (i > 0 ? i - 1 : items.length - 1))
      return
    }
    if (key.downArrow) {
      setIndex(i => (i < items.length - 1 ? i + 1 : 0))
      return
    }
    if (key.return && items.length > 0) {
      onSelect(items[Math.min(index, items.length - 1)].key)
    }
  })

  return (
    <Box flexDirection="column" paddingX={1}>
      <Text bold>{title}</Text>
      {items.length === 0 ? (
        <Text dimColor>(none)</Text>
      ) : (
        items.map((item, i) => (
          <Text key={item.key} color={i === index ? 'cyan' : undefined}>
            {i === index ? '›' : ' '} {item.label}
          </Text>
        ))
      )}
      {footer ? <Text dimColor>{footer}</Text> : null}
    </Box>
  )
}
