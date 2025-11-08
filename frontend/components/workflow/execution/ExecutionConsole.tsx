"use client"

import React, { useState, useEffect, useRef } from 'react'
import { Play, Square, Download, Filter, Search, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

interface BlockLog {
  block_id: string
  block_type: string
  block_name: string
  timestamp: string
  success: boolean
  inputs: Record<string, any>
  outputs: Record<string, any>
  error?: string
  error_type?: string
  duration_ms?: number
  metadata: Record<string, any>
}

interface ExecutionLog {
  id: string
  workflow_id: string
  execution_id: string
  trigger: string
  started_at: string
  ended_at?: string
  duration_ms?: number
  execution_data: {
    block_logs: BlockLog[]
    block_states: Record<string, any>
  }
  cost?: {
    total_tokens: number
    prompt_tokens: number
    completion_tokens: number
    estimated_cost: number
  }
  files?: Record<string, any>
  status: 'running' | 'completed' | 'failed' | 'timeout'
  error_message?: string
  created_at: string
}

interface ExecutionConsoleProps {
  workflowId: string
  executionId?: string
  autoRefresh?: boolean
  refreshInterval?: number
}

export function ExecutionConsole({
  workflowId,
  executionId,
  autoRefresh = true,
  refreshInterval = 2000,
}: ExecutionConsoleProps) {
  const [executions, setExecutions] = useState<ExecutionLog[]>([])
  const [selectedExecution, setSelectedExecution] = useState<ExecutionLog | null>(null)
  const [loading, setLoading] = useState(true)
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedBlocks, setExpandedBlocks] = useState<Set<string>>(new Set())
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    loadExecutions()

    if (autoRefresh && selectedExecution?.status === 'running') {
      intervalRef.current = setInterval(loadExecutions, refreshInterval)
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [workflowId, executionId, autoRefresh, selectedExecution?.status])

  const loadExecutions = async () => {
    try {
      const params = new URLSearchParams({ workflow_id: workflowId })
      if (executionId) {
        params.append('execution_id', executionId)
      }

      const response = await fetch(`/api/agent-builder/executions?${params}`)
      if (!response.ok) throw new Error('Failed to load executions')

      const data = await response.json()
      setExecutions(data.executions || [])

      // Auto-select if executionId provided or select most recent
      if (executionId) {
        const execution = data.executions.find((e: ExecutionLog) => e.execution_id === executionId)
        if (execution) setSelectedExecution(execution)
      } else if (data.executions.length > 0 && !selectedExecution) {
        setSelectedExecution(data.executions[0])
      }
    } catch (error) {
      console.error('Error loading executions:', error)
    } finally {
      setLoading(false)
    }
  }

  const exportExecution = () => {
    if (!selectedExecution) return

    const dataStr = JSON.stringify(selectedExecution, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `execution-${selectedExecution.execution_id}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const toggleBlockExpansion = (blockId: string) => {
    setExpandedBlocks(prev => {
      const next = new Set(prev)
      if (next.has(blockId)) {
        next.delete(blockId)
      } else {
        next.add(blockId)
      }
      return next
    })
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'running':
        return <Clock className="w-5 h-5 text-blue-500 animate-spin" />
      default:
        return <AlertCircle className="w-5 h-5 text-yellow-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      case 'running':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      default:
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
    }
  }

  const formatDuration = (ms?: number) => {
    if (!ms) return 'N/A'
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`
    return `${(ms / 60000).toFixed(2)}m`
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }

  const filteredExecutions = executions.filter(exec => {
    if (filterStatus !== 'all' && exec.status !== filterStatus) return false
    if (searchQuery && !exec.execution_id.toLowerCase().includes(searchQuery.toLowerCase())) return false
    return true
  })

  const blockLogs = selectedExecution?.execution_data?.block_logs || []

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="flex h-full gap-4">
      {/* Execution List Sidebar */}
      <div className="w-80 flex flex-col bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="font-semibold mb-3">Execution History</h3>
          
          {/* Filters */}
          <div className="space-y-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search executions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-sm"
              />
            </div>
            
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-sm"
            >
              <option value="all">All Status</option>
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="timeout">Timeout</option>
            </select>
          </div>
        </div>

        {/* Execution List */}
        <div className="flex-1 overflow-y-auto">
          {filteredExecutions.length === 0 ? (
            <div className="p-4 text-center text-gray-500 text-sm">
              No executions found
            </div>
          ) : (
            filteredExecutions.map((execution) => (
              <button
                key={execution.id}
                onClick={() => setSelectedExecution(execution)}
                className={`w-full p-3 text-left border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                  selectedExecution?.id === execution.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-mono text-gray-600 dark:text-gray-400">
                    {execution.execution_id.slice(0, 8)}...
                  </span>
                  {getStatusIcon(execution.status)}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {formatTimestamp(execution.started_at)}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Duration: {formatDuration(execution.duration_ms)}
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Execution Details */}
      <div className="flex-1 flex flex-col bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        {!selectedExecution ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            Select an execution to view details
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <h3 className="font-semibold">Execution Details</h3>
                  <span className={`px-2 py-1 text-xs rounded ${getStatusColor(selectedExecution.status)}`}>
                    {selectedExecution.status}
                  </span>
                </div>
                <button
                  onClick={exportExecution}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Export
                </button>
              </div>

              {/* Execution Metadata */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Execution ID:</span>
                  <div className="font-mono">{selectedExecution.execution_id}</div>
                </div>
                <div>
                  <span className="text-gray-500">Trigger:</span>
                  <div className="capitalize">{selectedExecution.trigger}</div>
                </div>
                <div>
                  <span className="text-gray-500">Started:</span>
                  <div>{formatTimestamp(selectedExecution.started_at)}</div>
                </div>
                <div>
                  <span className="text-gray-500">Duration:</span>
                  <div>{formatDuration(selectedExecution.duration_ms)}</div>
                </div>
              </div>

              {/* Cost Information */}
              {selectedExecution.cost && (
                <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Total Tokens:</span>
                      <div className="font-semibold">{selectedExecution.cost.total_tokens}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Prompt:</span>
                      <div>{selectedExecution.cost.prompt_tokens}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Completion:</span>
                      <div>{selectedExecution.cost.completion_tokens}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Cost:</span>
                      <div className="font-semibold">${selectedExecution.cost.estimated_cost.toFixed(4)}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Error Message */}
              {selectedExecution.error_message && (
                <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <div className="text-sm text-red-800 dark:text-red-200">
                    <strong>Error:</strong> {selectedExecution.error_message}
                  </div>
                </div>
              )}
            </div>

            {/* Block Logs */}
            <div className="flex-1 overflow-y-auto p-4">
              <h4 className="font-semibold mb-3">Execution Timeline</h4>
              
              {blockLogs.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  No block logs available
                </div>
              ) : (
                <div className="space-y-2">
                  {blockLogs.map((log, index) => (
                    <div
                      key={`${log.block_id}-${index}`}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
                    >
                      <button
                        onClick={() => toggleBlockExpansion(`${log.block_id}-${index}`)}
                        className="w-full p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            {log.success ? (
                              <CheckCircle className="w-4 h-4 text-green-500" />
                            ) : (
                              <XCircle className="w-4 h-4 text-red-500" />
                            )}
                            <div>
                              <div className="font-medium">{log.block_name}</div>
                              <div className="text-xs text-gray-500">{log.block_type}</div>
                            </div>
                          </div>
                          <div className="text-right text-sm">
                            <div className="text-gray-500">{formatDuration(log.duration_ms)}</div>
                            <div className="text-xs text-gray-400">
                              {new Date(log.timestamp).toLocaleTimeString()}
                            </div>
                          </div>
                        </div>
                      </button>

                      {expandedBlocks.has(`${log.block_id}-${index}`) && (
                        <div className="p-3 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
                          {/* Inputs */}
                          {Object.keys(log.inputs).length > 0 && (
                            <div className="mb-3">
                              <div className="text-xs font-semibold text-gray-500 mb-1">INPUTS</div>
                              <pre className="text-xs bg-white dark:bg-gray-800 p-2 rounded border border-gray-200 dark:border-gray-700 overflow-x-auto">
                                {JSON.stringify(log.inputs, null, 2)}
                              </pre>
                            </div>
                          )}

                          {/* Outputs */}
                          {Object.keys(log.outputs).length > 0 && (
                            <div className="mb-3">
                              <div className="text-xs font-semibold text-gray-500 mb-1">OUTPUTS</div>
                              <pre className="text-xs bg-white dark:bg-gray-800 p-2 rounded border border-gray-200 dark:border-gray-700 overflow-x-auto">
                                {JSON.stringify(log.outputs, null, 2)}
                              </pre>
                            </div>
                          )}

                          {/* Error */}
                          {log.error && (
                            <div>
                              <div className="text-xs font-semibold text-red-500 mb-1">ERROR</div>
                              <pre className="text-xs bg-red-50 dark:bg-red-900/20 p-2 rounded border border-red-200 dark:border-red-800 overflow-x-auto text-red-800 dark:text-red-200">
                                {log.error}
                              </pre>
                            </div>
                          )}

                          {/* Metadata */}
                          {Object.keys(log.metadata).length > 0 && (
                            <div className="mt-3">
                              <div className="text-xs font-semibold text-gray-500 mb-1">METADATA</div>
                              <pre className="text-xs bg-white dark:bg-gray-800 p-2 rounded border border-gray-200 dark:border-gray-700 overflow-x-auto">
                                {JSON.stringify(log.metadata, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
