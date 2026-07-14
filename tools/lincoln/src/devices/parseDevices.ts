export interface DeviceList {
  defaultDevice: string | null
  devices: string[]
}

const DEFAULT_PREFIX = 'Default input: '

export function parseDevicesOutput(output: string): DeviceList {
  let defaultDevice: string | null = null
  const devices: string[] = []

  for (const rawLine of output.split('\n')) {
    const line = rawLine.trim()
    if (!line) continue

    if (line.startsWith(DEFAULT_PREFIX)) {
      defaultDevice = line.slice(DEFAULT_PREFIX.length).trim() || null
      continue
    }

    devices.push(line)
  }

  return { defaultDevice, devices }
}
