import { Box, useApp } from 'ink'
import React, { useCallback, useEffect, useMemo, useState } from 'react'

import { StatusPanel } from './StatusPanel'
import { LogView, type LogEntry } from './LogView'
import { HintBar } from './HintBar'
import { useKeyHandler } from '../hooks/useKeyHandler'
import { useRecorder } from '../recording/useRecorder'

export interface RecordingAppProps {
  workspaceRoot: string
  sessionId: string
  topic: string
  designId: string
  branch: string
  audioMeterStyle?: 'bar' | 'dot' | 'wave'
  lincolnRecordPath?: string
}

function createLogId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

export function RecordingApp({
  workspaceRoot,
  sessionId,
  topic,
  designId,
  branch,
  audioMeterStyle = 'bar',
  lincolnRecordPath,
}: RecordingAppProps) {
  const { exit } = useApp()
  const [logs, setLogs] = useState<LogEntry[]>([])
  const addLog = useCallback((message: string, type: LogEntry['type'] = 'info') => {
    setLogs(prev => [...prev, { id: createLogId(), message, type }])
  }, [])

  const { state, start, stop, cancel } = useRecorder({
    workspaceRoot,
    sessionId,
    lincolnRecordPath,
    startOnMount: false,
  })

  useEffect(() => {
    switch (state.status) {
      case 'recording':
        addLog('Recording started.', 'info')
        break
      case 'stopped':
        addLog(`Saved to ${workspaceRoot}/${sessionId}/audio.wav`, 'success')
        addLog(`Run: claude process-interview ${sessionId}`, 'command')
        break
      case 'cancelled':
        addLog('Recording cancelled. No files were saved.', 'error')
        break
      case 'error':
        addLog(`Recording error: ${state.errorMessage ?? 'unknown error'}`, 'error')
        break
    }
  }, [state.status, state.errorMessage, addLog, workspaceRoot, sessionId])

  const handleQuit = useCallback(() => {
    exit()
  }, [exit])

  const handleRecord = useCallback(() => {
    if (state.status === 'idle') {
      start()
    }
  }, [state.status, start])

  const handleStop = useCallback(() => {
    if (state.status === 'recording') {
      stop().catch(() => {})
    }
  }, [state.status, stop])

  const handleCancel = useCallback(() => {
    if (state.status === 'recording') {
      cancel().catch(() => {})
    }
  }, [state.status, cancel])

  const handleDevices = useCallback(() => {
    addLog('Devices menu is not implemented yet. Run lincoln-record devices.', 'info')
  }, [addLog])

  const handleModel = useCallback(() => {
    addLog('Model menu is not implemented yet. Run lincoln-record warmup --model <name>.', 'info')
  }, [addLog])

  const isTerminal = state.status === 'stopped' || state.status === 'cancelled' || state.status === 'error'

  useKeyHandler({
    onRecord: handleRecord,
    onStop: handleStop,
    onCancel: handleCancel,
    onQuit: handleQuit,
    onDevices: handleDevices,
    onModel: handleModel,
    onAnyKey: isTerminal ? handleQuit : undefined,
  })

  const hintMode = useMemo(() => {
    if (state.status === 'idle') return 'idle'
    if (state.status === 'recording') return 'recording'
    if (state.status === 'stopped') return 'stopped'
    if (state.status === 'cancelled') return 'cancelled'
    return 'error'
  }, [state.status])

  return (
    <Box flexDirection="column" borderStyle="round" borderColor="gray" height={24}>
      <StatusPanel
        sessionId={sessionId}
        topic={topic}
        designId={designId}
        branch={branch}
        status={state.status}
        duration={state.duration}
      />
      <LogView logs={logs} />
      <Box flexGrow={1} />
      {state.status === 'recording' && audioMeterStyle ? null : null}
      <HintBar mode={hintMode} />
    </Box>
  )
}
