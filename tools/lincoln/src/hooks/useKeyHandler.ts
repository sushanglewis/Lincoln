import { useInput } from 'ink'

export interface KeyHandlerOptions {
  onStop: () => void
  onCancel: () => void
}

export function useKeyHandler({ onStop, onCancel }: KeyHandlerOptions) {
  useInput((input, key) => {
    if (key.return || input === '\r' || input === '\n') {
      onStop()
      return
    }

    if (input === 'q' || input === 'Q') {
      onCancel()
      return
    }

    if ((key.ctrl && input === 'c') || input === '') {
      onCancel()
    }
  })
}
