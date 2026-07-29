#!/usr/bin/env node
import { Box, Text } from 'ink'
import React from 'react'

import { parseArgs } from './config/args'
import { resolveConfig } from './config/resolveConfig'
import { InstallerApp } from './components/InstallerApp'

export interface AppProps {
  args: ReturnType<typeof parseArgs>
  config: ReturnType<typeof resolveConfig>
}

export function App({ args, config }: AppProps) {
  if (args.help) {
    return (
      <Box flexDirection="column" padding={1}>
        <Text bold>lincoln-install</Text>
        <Text>Terminal TUI installer for Lincoln.</Text>
        <Text />
        <Text bold>Usage:</Text>
        <Text>  npx lincoln-install [options]</Text>
        <Text />
        <Text bold>Options:</Text>
        <Text>  --root        Project root directory (default: current dir)</Text>
        <Text>  --harness     Target harness to generate (repeatable)</Text>
        <Text>  --yes         Auto-confirm all prompts</Text>
        <Text>  --dry-run     Show what would be done without executing</Text>
        <Text>  --no-tui      Print resolved config as JSON and exit</Text>
        <Text>  --format      Output format: human|json (default: human)</Text>
        <Text>  --help, -h    Show this help message</Text>
      </Box>
    )
  }

  return <InstallerApp config={config} />
}

export async function main(argv: string[] = process.argv.slice(2)): Promise<void> {
  try {
    const args = parseArgs(argv)

    if (args.help) {
      const { render } = await import('ink')
      render(<App args={args} config={{ root: process.cwd(), harnesses: [], yes: false, dryRun: false, format: args.format }} />)
      return
    }

    const config = resolveConfig(args)

    if (args.noTui) {
      console.log(JSON.stringify(config, null, 2))
      return
    }

    const { render } = await import('ink')
    render(<App args={args} config={config} />)
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    console.error(`Error: ${message}`)
    process.exitCode = 1
  }
}
