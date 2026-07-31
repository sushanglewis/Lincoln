export interface HarnessInfo {
  id: string
  name: string
  description: string
  installed: boolean
  projectDir?: string
  globalDir?: string
}

export interface SetupStep {
  command: string
  label: string
}

export interface SetupResult {
  success: boolean
  step?: string
  error?: string
}
