import { Box, Text, useInput } from 'ink'
import React, { useEffect, useState } from 'react'

import { SelectMenu } from './SelectMenu'
import type { DeviceList } from '../devices/parseDevices'

export interface DevicesMenuProps {
  listDevicesFn: () => Promise<DeviceList>
  onSelect: (device: string) => void
  onClose: () => void
}

type LoadState =
  | { status: 'loading' }
  | { status: 'loaded'; list: DeviceList }
  | { status: 'error'; message: string }

export function DevicesMenu({ listDevicesFn, onSelect, onClose }: DevicesMenuProps) {
  const [loadState, setLoadState] = useState<LoadState>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false
    listDevicesFn()
      .then(list => {
        if (!cancelled) setLoadState({ status: 'loaded', list })
      })
      .catch(error => {
        if (!cancelled) {
          setLoadState({
            status: 'error',
            message: error instanceof Error ? error.message : String(error),
          })
        }
      })
    return () => {
      cancelled = true
    }
  }, [listDevicesFn])

  useInput(
    (_input, key) => {
      if (key.escape) onClose()
    },
    { isActive: loadState.status !== 'loaded' },
  )

  if (loadState.status === 'loading') {
    return (
      <Box paddingX={1}>
        <Text dimColor>Loading devices…</Text>
      </Box>
    )
  }

  if (loadState.status === 'error') {
    return (
      <Box flexDirection="column" paddingX={1}>
        <Text color="red">Failed to list devices: {loadState.message}</Text>
        <Text dimColor>[esc] back</Text>
      </Box>
    )
  }

  const { list } = loadState
  const items = list.devices.map(name => ({
    key: name,
    label: name === list.defaultDevice ? `${name} (default)` : name,
  }))

  return (
    <SelectMenu
      title="Devices"
      items={items}
      onSelect={onSelect}
      onClose={onClose}
      footer="[↑↓] select  [enter] confirm  [esc] back"
    />
  )
}
