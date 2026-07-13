export interface WarmupProgress {
  downloaded: number
  total: number | null
  percent: number | null
}

const PROGRESS_WITH_TOTAL = /downloaded (\d+) \/ (\d+) bytes \(([\d.]+)%\)/
const PROGRESS_WITHOUT_TOTAL = /downloaded (\d+) bytes/

export function parseWarmupProgress(chunk: string): WarmupProgress | null {
  const withTotal = PROGRESS_WITH_TOTAL.exec(chunk)
  if (withTotal) {
    return {
      downloaded: Number(withTotal[1]),
      total: Number(withTotal[2]),
      percent: Number(withTotal[3]),
    }
  }

  const withoutTotal = PROGRESS_WITHOUT_TOTAL.exec(chunk)
  if (withoutTotal) {
    return {
      downloaded: Number(withoutTotal[1]),
      total: null,
      percent: null,
    }
  }

  return null
}
