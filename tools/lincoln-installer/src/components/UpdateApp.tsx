import { Box, Text, useInput, useApp } from 'ink'
import React, { useEffect, useState } from 'react'

import { updateRelease, type UpdateResult } from '../utils/updateRelease'

export interface UpdateAppProps {
  root: string
  repo: string
  dryRun: boolean
}

type UpdatePhase = 'welcome' | 'confirm' | 'running' | 'result'

export function UpdateApp({ root, repo, dryRun }: UpdateAppProps) {
  const { exit } = useApp()
  const [phase, setPhase] = useState<UpdatePhase>('welcome')
  const [result, setResult] = useState<UpdateResult | undefined>(undefined)

  useEffect(() => {
    async function check(): Promise<void> {
      const checkResult = await updateRelease({ root, repo, dryRun: true })
      setResult(checkResult)
      if (!checkResult.success) {
        setPhase('result')
        return
      }
      if (checkResult.fromVersion === checkResult.toVersion) {
        setPhase('result')
      } else {
        setPhase(dryRun ? 'result' : 'confirm')
      }
    }
    check()
  }, [root, repo, dryRun])

  useInput((input, key) => {
    if (phase === 'confirm' && key.return) {
      setPhase('running')
      updateRelease({ root, repo, dryRun })
        .then((applyResult) => {
          setResult(applyResult)
          setPhase('result')
        })
        .catch((err) => {
          setResult({
            success: false,
            updated: [],
            preserved: [],
            error: err instanceof Error ? err.message : String(err),
          })
          setPhase('result')
        })
    }

    if (phase === 'result' && key.return) {
      exit()
    }
  })

  if (phase === 'welcome') {
    return (
      <Box flexDirection="column" padding={1}>
        <Text bold>Lincoln Update</Text>
        <Text dimColor>Checking for the latest release...</Text>
      </Box>
    )
  }

  if (phase === 'confirm' && result?.success) {
    return (
      <Box flexDirection="column" padding={1}>
        <Text bold>Update available</Text>
        <Text>
          Current: {result.fromVersion} → Latest: {result.toVersion}
        </Text>
        <Text>Press Enter to apply the update, or Ctrl+C to cancel.</Text>
      </Box>
    )
  }

  if (phase === 'running') {
    return (
      <Box flexDirection="column" padding={1}>
        <Text bold>Updating Lincoln...</Text>
        <Text dimColor>Downloading and applying the latest release.</Text>
      </Box>
    )
  }

  if (!result) {
    return null
  }

  return (
    <Box flexDirection="column" padding={1}>
      {result.success && result.fromVersion === result.toVersion ? (
        <Text color="green">✓ Lincoln is up to date ({result.fromVersion}).</Text>
      ) : result.success && dryRun ? (
        <>
          <Text color="cyan">◌ Dry run: {result.fromVersion} → {result.toVersion} available.</Text>
          <Text>Re-run without --dry-run to apply the update.</Text>
        </>
      ) : result.success ? (
        <>
          <Text color="green">✓ Update complete: {result.fromVersion} → {result.toVersion}.</Text>
          {result.updated.length > 0 && (
            <Box flexDirection="column" marginTop={1}>
              <Text bold>Updated files:</Text>
              {result.updated.slice(0, 10).map((file) => (
                <Text key={file}>  {file}</Text>
              ))}
              {result.updated.length > 10 && <Text dimColor>  ...and {result.updated.length - 10} more.</Text>}
            </Box>
          )}
          {result.preserved.length > 0 && (
            <Box flexDirection="column" marginTop={1}>
              <Text bold>Preserved user data:</Text>
              {result.preserved.map((path) => (
                <Text key={path}>  {path}</Text>
              ))}
            </Box>
          )}
        </>
      ) : (
        <>
          <Text color="red">✗ Update failed.</Text>
          {result.error && <Text>{result.error}</Text>}
        </>
      )}
      <Box marginTop={1}>
        <Text dimColor>Press Enter to exit.</Text>
      </Box>
    </Box>
  )
}
