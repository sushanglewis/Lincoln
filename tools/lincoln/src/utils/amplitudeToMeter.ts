export function amplitudeToMeter(amplitude: number, maxBars: number): number {
  const clamped = Math.max(0, Math.min(1, amplitude))
  return Math.round(clamped * maxBars)
}
