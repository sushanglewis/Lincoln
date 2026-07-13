import { Box, useApp } from 'ink'
import React, { useCallback, useEffect, useMemo, useState } from 'react'

import { StatusPanel } from './StatusPanel'
import { LogView, type LogEntry } from './LogView'
import { HintBar } from './HintBar'
import { DevicesMenu } from './DevicesMenu'
import { ModelMenu } from './ModelMenu'
import { useKeyHandler } from '../hooks/useKeyHandler'
import { useRecorder } from '../recording/useRecorder'
import { listDevices } from '../devices/listDevices'
import { defaultModelCacheDir, listModelStatuses, type ModelStatus } from '../models/models'
import { runWarmup } from '../models/runWarmup'
import type { WarmupProgress } from '../models/warmupProgress'
import type { DeviceList } from '../devices/parseDevices'

type AppMode = 'main' | 'devices' | 'model'

export interface RecordingAppProps {
  workspaceRoot: string
  sessionId: string
  topic: string
  designId: string
  branch: string
  audioMeterStyle?: 'bar' | 'dot' | 'wave'
  lincolnRecordPath?: string
  listDevicesFn?: () => Promise<DeviceList>
  listModelStatusesFn?: () => Promise<ModelStatus[]>
  runWarmupFn?: (model: string, onProgress: (p: WarmupProgress) => void) => Promise<string>
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
  listDevicesFn,
  listModelStatusesFn,
  runWarmupFn,
}: RecordingAppProps) {
  const { exit } = useApp()
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [mode, setMode] = useState<AppMode>('main')
  const [mic, setMic] = useState<string | null>(null)
  const [model, setModel] = useState<string | null>(null)

  const addLog = useCallback((message: string, type: LogEntry['type'] = 'info') => {
    setLogs(prev => [...prev, { id: createLogId(), message, type }])
  }, [])

  const { state, start, stop, cancel } = useRecorder({
    workspaceRoot,
    sessionId,
    lincolnRecordPath,
    mic,
    model,
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
    if (state.status === 'idle') {
      setMode('devices')
    }
  }, [state.status])

  const handleModel = useCallback(() => {
    if (state.status === 'idle') {
      setMode('model')
    }
  }, [state.status])

  const handleDeviceSelect = useCallback(
    (device: string) => {
      setMic(device)
      addLog(`Input device: ${device}`, 'success')
      setMode('main')
    },
    [addLog],
  )

  const handleModelSelect = useCallback(
    (name: string) => {
      setModel(name)
      addLog(`Model: ${name}`, 'success')
      setMode('main')
    },
    [addLog],
  )

  const handleMenuClose = useCallback(() => {
    setMode('main')
  }, [])

  const isTerminal = state.status === 'stopped' || state.status === 'cancelled' || state.status === 'error'

  useKeyHandler({
    enabled: mode === 'main',
    onRecord: handleRecord,
    onStop: handleStop,
    onCancel: handleCancel,
    onQuit: handleQuit,
    onDevices: handleDevices,
    onModel: handleModel,
    onAnyKey: isTerminal ? handleQuit : undefined,
  })

  const hintMode = useMemo(() => {
    if (mode !== 'main') return 'menu'
    if (state.status === 'idle') return 'idle'
    if (state.status === 'recording') return 'recording'
    if (state.status === 'stopped') return 'stopped'
    if (state.status === 'cancelled') return 'cancelled'
    return 'error'
  }, [mode, state.status])

  const devicesLoader = useCallback(
    () => (listDevicesFn ?? (() => listDevices(lincolnRecordPath)))(),
    [listDevicesFn, lincolnRecordPath],
  )

  const modelsLoader = useCallback(
    () => (listModelStatusesFn ?? (() => Promise.resolve(listModelStatuses(defaultModelCacheDir()))))(),
    [listModelStatusesFn],
  )

  const warmupRunner = useCallback(
    (name: string, onProgress: (p: WarmupProgress) => void) =>
      runWarmupFn
        ? runWarmupFn(name, onProgress)
        : runWarmup({ model: name, lincolnRecordPath, onProgress }),
    [runWarmupFn, lincolnRecordPath],
  )

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
      {mode === 'devices' && (
        <DevicesMenu
          listDevicesFn={devicesLoader}
          onSelect={handleDeviceSelect}
          onClose={handleMenuClose}
        />
      )}
      {mode === 'model' && (
        <ModelMenu
          listModelStatusesFn={modelsLoader}
          runWarmupFn={warmupRunner}
          onSelect={handleModelSelect}
          onClose={handleMenuClose}
        />
      )}
      <LogView logs={logs} />
      <Box flexGrow={1} />
      <HintBar mode={hintMode} />
    </Box>
  )
}
