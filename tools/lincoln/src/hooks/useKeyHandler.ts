import { useInput } from 'ink'

export interface KeyHandlerOptions {
  onRecord?: () => void
  onStop?: () => void
  onCancel?: () => void
  onQuit?: () => void
  onDevices?: () => void
  onModel?: () => void
  onAnyKey?: () => void
}

export function useKeyHandler({
  onRecord,
  onStop,
  onCancel,
  onQuit,
  onDevices,
  onModel,
  onAnyKey,
}: KeyHandlerOptions) {
  useInput((input, key) => {
    if (key.escape || input === 'q' || input === 'Q') {
      onQuit?.()
      return
    }

    if (key.ctrl && input === 'c') {
      onQuit?.()
      return
    }

    switch (input) {
      case 'r':
      case 'R':
        onRecord?.()
        return
      case 's':
      case 'S':
        onStop?.()
        return
      case 'c':
      case 'C':
        onCancel?.()
        return
      case 'd':
      case 'D':
        onDevices?.()
        return
      case 'm':
      case 'M':
        onModel?.()
        return
    }

    onAnyKey?.()
  })
}
