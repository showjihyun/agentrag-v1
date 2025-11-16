'use client';

import React, { useState } from 'react';
import { X, Clock, CheckCircle2, XCircle, ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface NodeExecutionDetailsPanelProps {
  nodeId: string;
  nodeName: string;
  status: string;
  startTime?: number;
  endTime?: number;
  error?: string;
  input?: any;
  output?: any;
  logs?: string[];
  onClose: () => void;
}

export function NodeExecutionDetailsPanel({
  nodeId,
  nodeName,
  status,
  startTime,
  endTime,
  error,
  input,
  output,
  logs = [],
  onClose,
}: NodeExecutionDetailsPanelProps) {
  const [activeTab, setActiveTab] = useState<'input' | 'output' | 'logs'>('output');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['root']));
  const [copiedPath, setCopiedPath] = useState<string | null>(null);

  const duration = startTime && endTime 
    ? Math.floor((endTime - startTime) / 1000)
    : 0;

  const formatTime = (timestamp?: number) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleTimeString();
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const toggleSection = (path: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  const copyToClipboard = (text: string, path: string) => {
    navigator.clipboard.writeText(text);
    setCopiedPath(path);
    setTimeout(() => setCopiedPath(null), 2000);
  };

  const renderJSON = (data: any, path = 'root', level = 0): React.ReactNode => {
    if (data === null || data === undefined) {
      return <span className="text-gray-500">null</span>;
    }

    if (typeof data !== 'object') {
      return (
        <span className={`
          ${typeof data === 'string' ? 'text-green-600' : ''}
          ${typeof data === 'number' ? 'text-blue-600' : ''}
          ${typeof data === 'boolean' ? 'text-purple-600' : ''}
        `}>
          {typeof data === 'string' ? `"${data}"` : String(data)}
        </span>
      );
    }

    const isArray = Array.isArray(data);
    const entries = isArray ? data.map((v, i) => [i, v]) : Object.entries(data);
    const isExpanded = expandedSections.has(path);

    if (entries.length === 0) {
      return <span className="text-gray-500">{isArray ? '[]' : '{}'}</span>;
    }

    return (
      <div className="font-mono text-sm">
        <button
          onClick={() => toggleSection(path)}
          className="inline-flex items-center gap-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded px-1"
        >
          {isExpanded ? (
            <ChevronDown className="w-3 h-3" />
          ) : (
            <ChevronRight className="w-3 h-3" />
          )}
          <span className="text-gray-600">{isArray ? '[' : '{'}</span>
          {!isExpanded && (
            <span className="text-gray-400 text-xs">
              {entries.length} {isArray ? 'items' : 'keys'}
            </span>
          )}
        </button>

        {isExpanded && (
          <div className="ml-4 border-l-2 border-gray-200 dark:border-gray-700 pl-2">
            {entries.map(([key, value], index) => {
              const childPath = `${path}.${key}`;
              const valueStr = JSON.stringify(value);
              
              return (
                <div key={key} className="py-1 group">
                  <div className="flex items-start gap-2">
                    <span className="text-blue-600 font-medium">
                      {isArray ? `[${key}]` : `${key}:`}
                    </span>
                    <div className="flex-1">
                      {renderJSON(value, childPath, level + 1)}
                    </div>
                    <button
                      onClick={() => copyToClipboard(valueStr, childPath)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
                      title="Copy value"
                    >
                      {copiedPath === childPath ? (
                        <Check className="w-3 h-3 text-green-600" />
                      ) : (
                        <Copy className="w-3 h-3 text-gray-500" />
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {isExpanded && (
          <span className="text-gray-600">{isArray ? ']' : '}'}</span>
        )}
      </div>
    );
  };

  return (
    <div className="fixed right-0 top-0 bottom-0 w-[500px] bg-white dark:bg-gray-900 shadow-2xl border-l border-gray-200 dark:border-gray-800 flex flex-col z-50">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800">
        <div className="flex-1">
          <h3 className="font-semibold text-lg text-gray-900 dark:text-white">
            {nodeName}
          </h3>
          <p className="text-xs text-gray-500 font-mono">{nodeId}</p>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Status Bar */}
      <div className="p-4 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            {status === 'success' && <CheckCircle2 className="w-5 h-5 text-green-600" />}
            {status === 'failed' && <XCircle className="w-5 h-5 text-red-600" />}
            {status === 'running' && <Clock className="w-5 h-5 text-blue-600 animate-spin" />}
            <span className={`font-medium ${
              status === 'success' ? 'text-green-600' :
              status === 'failed' ? 'text-red-600' :
              status === 'running' ? 'text-blue-600' :
              'text-gray-600'
            }`}>
              {status.toUpperCase()}
            </span>
          </div>
          
          {duration > 0 && (
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <Clock className="w-4 h-4" />
              <span>{formatDuration(duration)}</span>
            </div>
          )}
        </div>

        {startTime && (
          <div className="mt-2 text-xs text-gray-500 space-y-1">
            <div>Started: {formatTime(startTime)}</div>
            {endTime && <div>Ended: {formatTime(endTime)}</div>}
          </div>
        )}

        {error && (
          <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-start gap-2">
              <XCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-red-800 dark:text-red-200">
                {error}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-800">
        <button
          onClick={() => setActiveTab('input')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === 'input'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50 dark:bg-blue-900/20'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800'
          }`}
        >
          Input
        </button>
        <button
          onClick={() => setActiveTab('output')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === 'output'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50 dark:bg-blue-900/20'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800'
          }`}
        >
          Output
        </button>
        <button
          onClick={() => setActiveTab('logs')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === 'logs'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50 dark:bg-blue-900/20'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800'
          }`}
        >
          Logs {logs.length > 0 && `(${logs.length})`}
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'input' && (
          <div>
            {input ? (
              renderJSON(input)
            ) : (
              <div className="text-center text-gray-500 py-8">
                No input data
              </div>
            )}
          </div>
        )}

        {activeTab === 'output' && (
          <div>
            {output ? (
              renderJSON(output)
            ) : (
              <div className="text-center text-gray-500 py-8">
                No output data
              </div>
            )}
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="space-y-2">
            {logs.length > 0 ? (
              logs.map((log, index) => (
                <div
                  key={index}
                  className="p-2 bg-gray-50 dark:bg-gray-800 rounded font-mono text-xs text-gray-700 dark:text-gray-300"
                >
                  {log}
                </div>
              ))
            ) : (
              <div className="text-center text-gray-500 py-8">
                No logs available
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800">
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              const data = activeTab === 'input' ? input : output;
              copyToClipboard(JSON.stringify(data, null, 2), 'full');
            }}
            className="flex-1"
          >
            <Copy className="w-4 h-4 mr-2" />
            Copy {activeTab === 'input' ? 'Input' : 'Output'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
            className="flex-1"
          >
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
