import { Box, Text, useInput } from 'ink'
import React, { useEffect, useState } from 'react'

import { SelectMenu } from './SelectMenu'
import type { ModelStatus } from '../models/models'
import type { WarmupProgress } from '../models/warmupProgress'

export interface ModelMenuProps {
  listModelStatusesFn: () => Promise<ModelStatus[]>
  runWarmupFn: (model: string, onProgress: (p: WarmupProgress) => void) => Promise<string>
  onSelect: (model: string) => void
  onClose: () => void
}

type MenuState =
  | { status: 'loading' }
  | { status: 'loaded'; models: ModelStatus[] }
  | { status: 'downloading'; model: string; percent: number | null; downloaded: number }
  | { status: 'error'; message: string }

export function ModelMenu({ listModelStatusesFn, runWarmupFn, onSelect, onClose }: ModelMenuProps) {
  const [menuState, setMenuState] = useState<MenuState>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false
    listModelStatusesFn()
      .then(models => {
        if (!cancelled) setMenuState({ status: 'loaded', models })
      })
      .catch(error => {
        if (!cancelled) {
          setMenuState({
            status: 'error',
            message: error instanceof Error ? error.message : String(error),
          })
        }
      })
    return () => {
      cancelled = true
    }
  }, [listModelStatusesFn])

  useInput(
    (_input, key) => {
      if (key.escape) onClose()
    },
    { isActive: menuState.status === 'error' },
  )

  const handleSelect = (name: string) => {
    if (menuState.status !== 'loaded') return
    const target = menuState.models.find(m => m.name === name)
    if (!target) return

    if (target.cached) {
      onSelect(name)
      return
    }

    setMenuState({ status: 'downloading', model: name, percent: null, downloaded: 0 })
    runWarmupFn(name, progress => {
      setMenuState({
        status: 'downloading',
        model: name,
        percent: progress.percent,
        downloaded: progress.downloaded,
      })
    })
      .then(() => onSelect(name))
      .catch(error => {
        setMenuState({
          status: 'error',
          message: error instanceof Error ? error.message : String(error),
        })
      })
  }

  if (menuState.status === 'loading') {
    return (
      <Box paddingX={1}>
        <Text dimColor>Loading models…</Text>
      </Box>
    )
  }

  if (menuState.status === 'error') {
    return (
      <Box flexDirection="column" paddingX={1}>
        <Text color="red">{menuState.message}</Text>
        <Text dimColor>[esc] back</Text>
      </Box>
    )
  }

  if (menuState.status === 'downloading') {
    const progressText =
      menuState.percent !== null
        ? `${menuState.percent.toFixed(1)}%`
        : `${menuState.downloaded} bytes`
    return (
      <Box flexDirection="column" paddingX={1}>
        <Text>Downloading model '{menuState.model}'… {progressText}</Text>
        <Text dimColor>please wait</Text>
      </Box>
    )
  }

  const items = menuState.models.map(m => ({
    key: m.name,
    label: m.cached ? `✓ ${m.name}` : `· ${m.name} (not downloaded)`,
  }))

  return (
    <SelectMenu
      title="Model"
      items={items}
      onSelect={handleSelect}
      onClose={onClose}
      footer="[↑↓] select  [enter] confirm  [esc] back"
    />
  )
}
