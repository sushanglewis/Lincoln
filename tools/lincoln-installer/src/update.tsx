#!/usr/bin/env node
import { Box, Text } from 'ink'
import React from 'react'

import { parseUpdateArgs } from './config/updateArgs'
import { UpdateApp } from './components/UpdateApp'
import { updateRelease, type UpdateResult } from './utils/updateRelease'

function printHumanResult(result: UpdateResult): void {
  if (!result.success) {
    console.log(`Update failed: ${result.error ?? 'unknown error'}`)
    return
  }
  if (result.fromVersion === result.toVersion) {
    console.log(`Lincoln is up to date (${result.fromVersion}).`)
    return
  }
  console.log(`Update available: ${result.fromVersion} → ${result.toVersion}`)
  if (result.updated.length > 0) {
    console.log(`Updated files (${result.updated.length}):`)
    for (const file of result.updated.slice(0, 10)) {
      console.log(`  ${file}`)
    }
    if (result.updated.length > 10) {
      console.log(`  ...and ${result.updated.length - 10} more`)
    }
  }
  if (result.preserved.length > 0) {
    console.log('Preserved user data:')
    for (const path of result.preserved) {
      console.log(`  ${path}`)
    }
  }
  if (result.backupDir) {
    console.log(`Backup directory: ${result.backupDir}`)
  }
}

export function UpdateAppRoot({ args }: { args: ReturnType<typeof parseUpdateArgs> }) {
  if (args.help) {
    return (
      <Box flexDirection="column" padding={1}>
        <Text bold>lincoln-update</Text>
        <Text>Update Lincoln to the latest release.</Text>
        <Text />
        <Text bold>Usage:</Text>
        <Text>  npx lincoln-update [options]</Text>
        <Text />
        <Text bold>Options:</Text>
        <Text>  --root        Project root directory (default: current dir)</Text>
        <Text>  --repo        GitHub repository slug (default: sushanglewis/Lincoln)</Text>
        <Text>  --dry-run     Show what would be updated without applying changes</Text>
        <Text>  --no-tui      Print result as JSON and exit</Text>
        <Text>  --format      Output format: human|json (default: human)</Text>
        <Text>  --help, -h    Show this help message</Text>
      </Box>
    )
  }

  return <UpdateApp root={args.root} repo={args.repo} dryRun={args.dryRun} />
}

export async function updateMain(argv: string[] = process.argv.slice(2)): Promise<void> {
  try {
    const args = parseUpdateArgs(argv)

    if (args.help) {
      const { render } = await import('ink')
      render(<UpdateAppRoot args={args} />)
      return
    }

    if (args.noTui) {
      const result = await updateRelease({ root: args.root, repo: args.repo, dryRun: args.dryRun })
      if (args.format === 'human') {
        printHumanResult(result)
      } else {
        console.log(JSON.stringify(result, null, 2))
      }
      return
    }

    const { render } = await import('ink')
    render(<UpdateAppRoot args={args} />)
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    console.error(`Error: ${message}`)
    process.exitCode = 1
  }
}
