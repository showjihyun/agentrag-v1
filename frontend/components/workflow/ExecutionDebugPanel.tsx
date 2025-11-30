'use client';

import React, { useState, useMemo } from 'react';
import {
  Bug,
  ChevronDown,
  ChevronRight,
  Copy,
  Download,
  Search,
  Filter,
  Clock,
  AlertCircle,
  CheckCircle,
  XCircle,
  Info,
  Terminal,
  FileJson,
  Layers,
  RefreshCw,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

// Types
interface LogEntry {
  id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warning' | 'error';
  nodeId?: string;
  nodeName?: string;
  message: string;
  data?: any;
  traceId?: string;
}

interface NodeDebugInfo {
  nodeId: string;
  nodeName: string;
  nodeType: string;
  input: any;
  output: any;
  config: any;
  executionTime?: number;
  error?: string;
  stackTrace?: string;
  retries: number;
  logs: LogEntry[];
}

interface ExecutionDebugPanelProps {
  executionId: string;
  nodes: NodeDebugInfo[];
  logs: LogEntry[];
  onRefresh?: () => void;
  onExport?: () => void;
}

// Log level badge
const LogLevelBadge: React.FC<{ level: string }> = ({ level }) => {
  const config: Record<string, { color: string; icon: React.ReactNode }> = {
    debug: { color: 'bg-gray-100 text-gray-600', icon: <Bug className="w-3 h-3" /> },
    info: { color: 'bg-blue-100 text-blue-600', icon: <Info className="w-3 h-3" /> },
    warning: { color: 'bg-yellow-100 text-yellow-600', icon: <AlertCircle className="w-3 h-3" /> },
    error: { color: 'bg-red-100 text-red-600', icon: <XCircle className="w-3 h-3" /> },
  };

  const { color, icon } = config[level] || config.info;

  return (
    <span className={cn('inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium', color)}>
      {icon}
      {level.toUpperCase()}
    </span>
  );
};

// JSON Viewer component
const JsonViewer: React.FC<{ data: any; maxHeight?: string }> = ({ data, maxHeight = '200px' }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (data === undefined || data === null) {
    return <span className="text-gray-400 text-sm italic">없음</span>;
  }

  return (
    <div className="relative group">
      <pre 
        className="p-2 bg-gray-900 text-gray-100 rounded text-xs overflow-auto font-mono"
        style={{ maxHeight }}
      >
        {JSON.stringify(data, null, 2)}
      </pre>
      <button
        onClick={handleCopy}
        className="absolute top-2 right-2 p-1 bg-gray-700 rounded opacity-0 group-hover:opacity-100 transition-opacity"
        title="복사"
      >
        <Copy className="w-3 h-3 text-gray-300" />
      </button>
      {copied && (
        <span className="absolute top-2 right-10 text-xs text-green-400">복사됨!</span>
      )}
    </div>
  );
};

// Node debug card
const NodeDebugCard: React.FC<{ node: NodeDebugInfo }> = ({ node }) => {
  const [expanded, setExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<'input' | 'output' | 'config' | 'logs'>('input');

  const hasError = !!node.error;

  return (
    <div className={cn(
      'border rounded-lg overflow-hidden',
      hasError && 'border-red-300 bg-red-50'
    )}>
      {/* Header */}
      <div 
        className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          <div>
            <div className="font-medium text-sm flex items-center gap-2">
              {node.nodeName}
              {hasError && <XCircle className="w-4 h-4 text-red-500" />}
              {!hasError && node.output && <CheckCircle className="w-4 h-4 text-green-500" />}
            </div>
            <div className="text-xs text-gray-500">{node.nodeType} • {node.nodeId}</div>
          </div>
        </div>
        
        <div className="flex items-center gap-2 text-xs text-gray-500">
          {node.executionTime !== undefined && (
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {node.executionTime}ms
            </span>
          )}
          {node.retries > 0 && (
            <span className="flex items-center gap-1 text-orange-500">
              <RefreshCw className="w-3 h-3" />
              {node.retries}
            </span>
          )}
        </div>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t">
          {/* Tabs */}
          <div className="flex border-b bg-gray-50">
            {(['input', 'output', 'config', 'logs'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  'px-4 py-2 text-sm font-medium border-b-2 -mb-px',
                  activeTab === tab 
                    ? 'border-blue-500 text-blue-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                )}
              >
                {tab === 'input' && '입력'}
                {tab === 'output' && '출력'}
                {tab === 'config' && '설정'}
                {tab === 'logs' && `로그 (${node.logs.length})`}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="p-3">
            {activeTab === 'input' && <JsonViewer data={node.input} />}
            {activeTab === 'output' && <JsonViewer data={node.output} />}
            {activeTab === 'config' && <JsonViewer data={node.config} />}
            {activeTab === 'logs' && (
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {node.logs.length === 0 ? (
                  <div className="text-gray-400 text-sm italic">로그 없음</div>
                ) : (
                  node.logs.map(log => (
                    <div key={log.id} className="flex items-start gap-2 text-xs py-1 border-b last:border-0">
                      <span className="text-gray-400 font-mono whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                      <LogLevelBadge level={log.level} />
                      <span className="flex-1">{log.message}</span>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Error display */}
          {hasError && (
            <div className="p-3 border-t bg-red-50">
              <div className="text-sm font-medium text-red-700 mb-1">오류</div>
              <div className="text-sm text-red-600">{node.error}</div>
              {node.stackTrace && (
                <details className="mt-2">
                  <summary className="text-xs text-red-500 cursor-pointer">스택 트레이스</summary>
                  <pre className="mt-1 p-2 bg-red-100 rounded text-xs overflow-auto max-h-32 font-mono">
                    {node.stackTrace}
                  </pre>
                </details>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Main component
export const ExecutionDebugPanel: React.FC<ExecutionDebugPanelProps> = ({
  executionId,
  nodes,
  logs,
  onRefresh,
  onExport,
}) => {
  const [activeView, setActiveView] = useState<'nodes' | 'logs' | 'timeline'>('nodes');
  const [searchQuery, setSearchQuery] = useState('');
  const [logLevelFilter, setLogLevelFilter] = useState<string[]>(['debug', 'info', 'warning', 'error']);

  // Filter logs
  const filteredLogs = useMemo(() => {
    return logs.filter(log => {
      if (!logLevelFilter.includes(log.level)) return false;
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          log.message.toLowerCase().includes(query) ||
          log.nodeId?.toLowerCase().includes(query) ||
          log.nodeName?.toLowerCase().includes(query)
        );
      }
      return true;
    });
  }, [logs, logLevelFilter, searchQuery]);

  // Filter nodes
  const filteredNodes = useMemo(() => {
    if (!searchQuery) return nodes;
    const query = searchQuery.toLowerCase();
    return nodes.filter(node => 
      node.nodeName.toLowerCase().includes(query) ||
      node.nodeId.toLowerCase().includes(query) ||
      node.nodeType.toLowerCase().includes(query)
    );
  }, [nodes, searchQuery]);

  // Export debug data
  const handleExport = () => {
    const data = {
      executionId,
      exportedAt: new Date().toISOString(),
      nodes,
      logs,
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `debug-${executionId.slice(0, 8)}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    onExport?.();
  };

  return (
    <div className="bg-white rounded-lg border shadow-sm h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b flex-shrink-0">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Bug className="w-5 h-5 text-purple-500" />
            <h3 className="font-semibold">디버그 패널</h3>
          </div>
          <div className="flex items-center gap-2">
            {onRefresh && (
              <Button size="sm" variant="ghost" onClick={onRefresh}>
                <RefreshCw className="w-4 h-4" />
              </Button>
            )}
            <Button size="sm" variant="outline" onClick={handleExport}>
              <Download className="w-4 h-4 mr-1" />
              내보내기
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="노드, 로그 검색..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* View tabs */}
      <div className="flex border-b flex-shrink-0">
        <button
          onClick={() => setActiveView('nodes')}
          className={cn(
            'flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 -mb-px',
            activeView === 'nodes' 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700'
          )}
        >
          <Layers className="w-4 h-4" />
          노드 ({filteredNodes.length})
        </button>
        <button
          onClick={() => setActiveView('logs')}
          className={cn(
            'flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 -mb-px',
            activeView === 'logs' 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700'
          )}
        >
          <Terminal className="w-4 h-4" />
          로그 ({filteredLogs.length})
        </button>
        <button
          onClick={() => setActiveView('timeline')}
          className={cn(
            'flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 -mb-px',
            activeView === 'timeline' 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700'
          )}
        >
          <Clock className="w-4 h-4" />
          타임라인
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* Nodes view */}
        {activeView === 'nodes' && (
          <div className="space-y-2">
            {filteredNodes.map(node => (
              <NodeDebugCard key={node.nodeId} node={node} />
            ))}
            {filteredNodes.length === 0 && (
              <div className="text-center text-gray-400 py-8">
                {searchQuery ? '검색 결과가 없습니다' : '노드 정보가 없습니다'}
              </div>
            )}
          </div>
        )}

        {/* Logs view */}
        {activeView === 'logs' && (
          <div>
            {/* Log level filter */}
            <div className="flex items-center gap-2 mb-3">
              <Filter className="w-4 h-4 text-gray-400" />
              {(['debug', 'info', 'warning', 'error'] as const).map(level => (
                <button
                  key={level}
                  onClick={() => {
                    setLogLevelFilter(prev => 
                      prev.includes(level) 
                        ? prev.filter(l => l !== level)
                        : [...prev, level]
                    );
                  }}
                  className={cn(
                    'px-2 py-1 rounded text-xs font-medium transition-colors',
                    logLevelFilter.includes(level) 
                      ? 'bg-blue-100 text-blue-700' 
                      : 'bg-gray-100 text-gray-500'
                  )}
                >
                  {level.toUpperCase()}
                </button>
              ))}
            </div>

            {/* Log entries */}
            <div className="space-y-1 font-mono text-xs">
              {filteredLogs.map(log => (
                <div 
                  key={log.id} 
                  className={cn(
                    'flex items-start gap-2 p-2 rounded hover:bg-gray-50',
                    log.level === 'error' && 'bg-red-50',
                    log.level === 'warning' && 'bg-yellow-50'
                  )}
                >
                  <span className="text-gray-400 whitespace-nowrap">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  <LogLevelBadge level={log.level} />
                  {log.nodeName && (
                    <span className="text-purple-600 whitespace-nowrap">[{log.nodeName}]</span>
                  )}
                  <span className="flex-1 break-all">{log.message}</span>
                </div>
              ))}
              {filteredLogs.length === 0 && (
                <div className="text-center text-gray-400 py-8">
                  로그가 없습니다
                </div>
              )}
            </div>
          </div>
        )}

        {/* Timeline view */}
        {activeView === 'timeline' && (
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
            
            {/* Timeline items */}
            <div className="space-y-4">
              {nodes.map((node, index) => (
                <div key={node.nodeId} className="relative flex items-start gap-4 pl-8">
                  {/* Timeline dot */}
                  <div className={cn(
                    'absolute left-2.5 w-3 h-3 rounded-full border-2 bg-white',
                    node.error ? 'border-red-500' : node.output ? 'border-green-500' : 'border-gray-300'
                  )} />
                  
                  {/* Content */}
                  <div className="flex-1 pb-4">
                    <div className="flex items-center justify-between">
                      <div className="font-medium text-sm">{node.nodeName}</div>
                      {node.executionTime !== undefined && (
                        <span className="text-xs text-gray-500">{node.executionTime}ms</span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500">{node.nodeType}</div>
                    {node.error && (
                      <div className="mt-1 text-xs text-red-600">{node.error}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t bg-gray-50 text-xs text-gray-500 flex-shrink-0">
        <div className="flex items-center justify-between">
          <span>실행 ID: {executionId}</span>
          <span>노드: {nodes.length} | 로그: {logs.length}</span>
        </div>
      </div>
    </div>
  );
};

export default ExecutionDebugPanel;
