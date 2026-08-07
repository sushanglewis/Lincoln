import { install as runInstall } from './commands/install.js'
import { createPrompt } from './lib/prompt.js'

export interface PostinstallDeps {
  isTTY: boolean
  confirm: (question: string) => Promise<boolean>
  install: () => Promise<number>
  env: Record<string, string | undefined>
}

function isSkipped(env: Record<string, string | undefined>): boolean {
  if (env.CI) {
    return true
  }
  if (env.NODE_ENV === 'test') {
    return true
  }
  if (env.LINCOLN_SKIP_POSTINSTALL) {
    return true
  }
  return false
}

export function createDefaultDeps(): PostinstallDeps {
  return {
    isTTY: Boolean(process.stdin.isTTY && process.stdout.isTTY),
    confirm: async (question: string) => {
      const prompt = createPrompt()
      try {
        return await prompt.confirm(question, true)
      } finally {
        prompt.close()
      }
    },
    install: async () =>
      runInstall({ yes: false, dryRun: false, force: false, harnesses: [], noVenv: false, noInteractive: false }),
    env: process.env
  }
}

export async function runPostinstall(deps: PostinstallDeps = createDefaultDeps()): Promise<number> {
  if (isSkipped(deps.env)) {
    return 0
  }

  if (!deps.isTTY) {
    console.log('Lincoln installed globally.')
    console.log('Run "lincoln install" to finish setup.')
    return 0
  }

  try {
    const ok = await deps.confirm('Configure Lincoln harnesses now?')
    if (!ok) {
      console.log('Run "lincoln install" anytime to finish setup.')
      return 0
    }
    await deps.install()
    return 0
  } catch (err) {
    console.log('Lincoln installed globally.')
    console.log('Run "lincoln install" anytime to finish setup.')
    if (err instanceof Error) {
      console.error(`Postinstall setup skipped: ${err.message}`)
    }
    return 0
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runPostinstall()
    .then((code) => process.exit(code))
    .catch(() => process.exit(0))
}
