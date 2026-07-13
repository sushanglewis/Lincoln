import { execFile } from 'node:child_process'
import { promisify } from 'node:util'

import { parseDevicesOutput, type DeviceList } from './parseDevices'

const execFileAsync = promisify(execFile)

export async function listDevices(lincolnRecordPath = 'lincoln-record'): Promise<DeviceList> {
  const { stdout } = await execFileAsync(lincolnRecordPath, ['devices'])
  return parseDevicesOutput(stdout)
}
