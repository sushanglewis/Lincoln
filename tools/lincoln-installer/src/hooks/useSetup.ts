import { existsSync } from 'node:fs'
import { resolve } from 'node:path'
import { useCallback, useState } from 'react'

import { runSetup, parseJsonOutput, type RunSetupResult } from '../utils/runSetup'

export type SetupPhase =
  | 'welcome'
  | 'harness'
  | 'options'
  | 'summary'
  | 'running'
  | 'result'

export interface SetupOptions {
  root: string
  harnesses: string[]
  yes: boolean
  dryRun: boolean
}

export interface StepResult {
  step: string
  success: boolean
  output?: unknown
  error?: string
}

export interface UseSetupReturn {
  isRunning: boolean
  results: StepResult[]
  currentStep: string
  error?: string
  startSetup: (options: SetupOptions) => void
}

function getPythonCommand(): string {
  if (process.platform === 'win32') {
    return 'python'
  }
  return 'python3'
}

export function useSetup(): UseSetupReturn {
  const [isRunning, setIsRunning] = useState(false)
  const [results, setResults] = useState<StepResult[]>([])
  const [currentStep, setCurrentStep] = useState<string>('')
  const [error, setError] = useState<string | undefined>(undefined)

  const runStep = useCallback(
    async (label: string, command: string, args: string[], root: string): Promise<StepResult> => {
      setCurrentStep(label)
      const result: RunSetupResult = await runSetup({ root, command, args })
      const output = parseJsonOutput(result.stdout)
      const stepResult: StepResult = {
        step: label,
        success: result.success,
        output,
        error: result.error || (result.success ? undefined : result.stderr || 'unknown error'),
      }
      setResults((prev) => [...prev, stepResult])
      return stepResult
    },
    []
  )

  const startSetup = useCallback(
    (options: SetupOptions) => {
      setIsRunning(true)
      setResults([])
      setError(undefined)

      async function runAll(): Promise<void> {
        const setupScript = resolve(options.root, 'scripts', 'lincoln-setup.py')
        if (!existsSync(setupScript)) {
          throw new Error(
            `Lincoln setup script not found at ${setupScript}. ` +
              `Run lincoln-install inside a Lincoln project checkout.`
          )
        }

        const format = '--format=json'
        const rootArg = `--root=${options.root}`
        const yesArg = options.yes ? '--yes' : undefined
        const dryRunArg = options.dryRun ? '--dry-run' : undefined
        const commonArgs = [rootArg, format, yesArg, dryRunArg].filter(
          (arg): arg is string => arg !== undefined
        )

        const python = getPythonCommand()

        const check = await runStep('check', python, [setupScript, 'check', ...commonArgs], options.root)
        if (!check.success) {
          return
        }

        const skills = await runStep('install-skills', python, [setupScript, 'install-skills', ...commonArgs], options.root)
        if (!skills.success) {
          return
        }

        const clis = await runStep('install-clis', python, [setupScript, 'install-clis', ...commonArgs], options.root)
        if (!clis.success) {
          return
        }

        const config = await runStep('init-repo-config', python, [setupScript, 'init-repo-config', ...commonArgs], options.root)
        if (!config.success) {
          return
        }

        const project = await runStep('init-project', python, [setupScript, 'init-project', ...commonArgs], options.root)
        if (!project.success) {
          return
        }

        if (options.harnesses.length > 0) {
          const harnessArgs = options.harnesses.flatMap((h) => ['--harness', h])
          const harness = await runStep(
            'generate-harness',
            python,
            [setupScript, 'generate-harness', ...commonArgs, ...harnessArgs],
            options.root
          )
          if (!harness.success) {
            return
          }
        }
      }

      runAll()
        .catch((err) => {
          setError(err instanceof Error ? err.message : String(err))
        })
        .finally(() => {
          setIsRunning(false)
        })
    },
    [runStep]
  )

  return {
    isRunning,
    results,
    currentStep,
    error,
    startSetup,
  }
}
