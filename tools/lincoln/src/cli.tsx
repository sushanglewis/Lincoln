#!/usr/bin/env node
import { Box, Text } from 'ink'
import React from 'react'

import { parseArgs, type ParsedArgs } from './config/args'
import { resolveConfig, type ResolvedConfig } from './config/resolveConfig'

export interface AppProps {
  args: ParsedArgs
  config: ResolvedConfig
}

export function App({ args, config }: AppProps) {
  if (args.help) {
    return (
      <Box flexDirection="column" padding={1}>
        <Text bold>lincoln</Text>
        <Text>Cross-tool TUI for Lincoln interview recording.</Text>
        <Text />
        <Text bold>Usage:</Text>
        <Text>  lincoln [options]</Text>
        <Text />
        <Text bold>Options:</Text>
        <Text>  --topic       Interview topic</Text>
        <Text>  --design-id   Design ID for the session</Text>
        <Text>  --branch      Current branch name</Text>
        <Text>  --session-id  Explicit session ID</Text>
        <Text>  --no-tui      Run without the terminal UI</Text>
        <Text>  --help, -h    Show this help message</Text>
        <Text />
        <Text dimColor>Configuration files: ~/.lincolnrc, ./.lincolnrc</Text>
      </Box>
    )
  }

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold>Lincoln</Text>
      <Text>Session: {config.sessionId}</Text>
      <Text>Topic: {config.topic || '(none)'}</Text>
      <Text>Design: {config.designId || '(none)'}</Text>
      <Text>Branch: {config.branch || '(none)'}</Text>
      <Text dimColor>Press Enter to start recording...</Text>
    </Box>
  )
}

export async function main(argv: string[] = process.argv.slice(2)): Promise<void> {
  const args = parseArgs(argv)
  const config = resolveConfig(args)

  if (args.noTui) {
    console.log(JSON.stringify(config, null, 2))
    return
  }

  const { render } = await import('ink')
  render(<App args={args} config={config} />)
}
