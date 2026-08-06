import type { GlobalHarnessInfo, HarnessId } from './harnessDetect.js'
import type { MultiSelectOption } from './prompt.js'

export const HARNESS_LABELS: Record<HarnessId, string> = {
  'claude-code': 'Claude Code',
  codex: 'Codex',
  opencode: 'OpenCode'
}

export function buildHarnessOptions(
  detected: ReadonlyArray<GlobalHarnessInfo>
): MultiSelectOption[] {
  return detected.map((harness) => ({
    id: harness.id,
    label: HARNESS_LABELS[harness.id],
    checked: harness.installed
  }))
}

export function resolveHarnessSelection(
  detected: ReadonlyArray<GlobalHarnessInfo>,
  selection: string[] | undefined
): HarnessId[] {
  if (selection === undefined) {
    return detected.filter((harness) => harness.installed).map((harness) => harness.id)
  }
  const validIds = new Set<HarnessId>()
  for (const id of selection) {
    const match = detected.find((harness) => harness.id === id)
    if (match) {
      validIds.add(match.id)
    }
  }
  return Array.from(validIds)
}
