/**
 * Execution Log Viewer
 * 플러그인 실행 로그를 위한 고급 뷰어 컴포넌트
 */

'use client';

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuCheckboxItem,
} from '@/components/ui/dropdown-menu';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Terminal,
  Search,
  Filter,
  Download,
  RefreshCw,
  Play,
  Pause,
  Square,
  ChevronDown,
  ChevronRight,
  Copy,
  Eye,
  EyeOff,
  Calendar,
  Clock,
  AlertCircle,
  Info,
  AlertTriangle,
  XCircle,
  CheckCircle,
  Loader2,
  FileText,
  Settings,
  Maximize2,
  Minimize2,
} from 'lucide-react';
import { toast } from 'sonner';

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warning' | 'error' | 'trace';
  message: string;
  context?: Record<string, any>;
  execution_id?: string;
  plugin_id: string;
  source?: string;
  stack_trace?: string;
  user_id?: string;
  session_id?: string;
}

export interface LogFilter {
  level: string[];
  search: string;
  execution_id: string;
  source: string;
  user_id: string;
  timeRange: string;
  startTime?: string;
  endTime?: string;
}

interface ExecutionLogViewerProps {
  pluginId: string;
  executionId?: string;
  initialFilters?: Partial<LogFilter>;
  height?: number;
  showToolbar?: boolean;
  showFilters?: boolean;
  autoScroll?: boolean;
  realTime?: boolean;
  exportable?: boolean;
  searchable?: boolean;
  className?: string;
}

const LOG_LEVELS = [
  { value: 'trace', label: 'Trace', color: 'text-gray-500', bg: 'bg-gray-50' },
  { value: 'debug', label: 'Debug', color: 'text-blue-600', bg: 'bg-blue-50' },
  { value: 'info', label: 'Info', color: 'text-green-600', bg: 'bg-green-50' },
  { value: 'warning', label: 'Warning', color: 'text-yellow-600', bg: 'bg-yellow-50' },
  { value: 'error', label: 'Error', color: 'text-red-600', bg: 'bg-red-50' },
];

export function ExecutionLogViewer({
  pluginId,
  executionId,
  initialFilters = {},
  height = 400,
  showToolbar = true,
  showFilters = true,
  autoScroll = true,
  realTime = false,
  exportable = true,
  searchable = true,
  className,
}: ExecutionLogViewerProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [filters, setFilters] = useState<LogFilter>({
    level: ['info', 'warning', 'error'],
    search: '',
    execution_id: executionId || '',
    source: '',
    user_id: '',
    timeRange: '1h',
    ...initialFilters,
  });
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [autoScrollEnabled, setAutoScrollEnabled] = useState(autoScroll);
  const [showContext, setShowContext] = useState(false);
  const [highlightSearch, setHighlightSearch] = useState(true);

  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // 필터링된 로그
  const filteredLogs = useMemo(() => {
    return logs.filter(log => {
      // 레벨 필터
      if (filters.level.length > 0 && !filters.level.includes(log.level)) {
        return false;
      }

      // 검색 필터
      if (filters.search && !log.message.toLowerCase().includes(filters.search.toLowerCase())) {
        return false;
      }

      // 실행 ID 필터
      if (filters.execution_id && log.execution_id !== filters.execution_id) {
        return false;
      }

      // 소스 필터
      if (filters.source && log.source !== filters.source) {
        return false;
      }

      // 사용자 ID 필터
      if (filters.user_id && log.user_id !== filters.user_id) {
        return false;
      }

      return true;
    });
  }, [logs, filters]);

  // 로그 로딩
  const loadLogs = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        timeRange: filters.timeRange,
        ...(filters.execution_id && { execution_id: filters.execution_id }),
        ...(filters.source && { source: filters.source }),
        ...(filters.user_id && { user_id: filters.user_id }),
        ...(filters.startTime && { start_time: filters.startTime }),
        ...(filters.endTime && { end_time: filters.endTime }),
        limit: '1000',
      });

      const response = await fetch(`/api/agent-builder/plugins/${pluginId}/logs?${params}`);
      const data = await response.json();
      
      setLogs(data);
    } catch (error) {
      toast.error('Failed to load logs');
      console.error('Load logs error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 실시간 로그 스트리밍
  const startStreaming = () => {
    if (wsRef.current) return;

    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/api/agent-builder/plugins/${pluginId}/logs/stream`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsStreaming(true);
      // 필터 전송
      ws.send(JSON.stringify({ type: 'filter', filters }));
    };

    ws.onmessage = (event) => {
      const logEntry: LogEntry = JSON.parse(event.data);
      setLogs(prev => [...prev, logEntry]);
    };

    ws.onclose = () => {
      setIsStreaming(false);
      wsRef.current = null;
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsStreaming(false);
    };

    wsRef.current = ws;
  };

  const stopStreaming = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
      setIsStreaming(false);
    }
  };

  // 자동 스크롤
  useEffect(() => {
    if (autoScrollEnabled && scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [filteredLogs, autoScrollEnabled]);

  // 초기 로딩
  useEffect(() => {
    loadLogs();
    
    if (realTime) {
      startStreaming();
    }

    return () => {
      stopStreaming();
    };
  }, [pluginId, filters.timeRange, filters.execution_id]);

  // 필터 업데이트
  const updateFilter = (key: keyof LogFilter, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  // 로그 내보내기
  const exportLogs = async (format: 'csv' | 'json' | 'txt') => {
    try {
      const params = new URLSearchParams({
        format,
        timeRange: filters.timeRange,
        ...(filters.execution_id && { execution_id: filters.execution_id }),
        ...(filters.source && { source: filters.source }),
        ...(filters.user_id && { user_id: filters.user_id }),
      });

      const response = await fetch(`/api/agent-builder/plugins/${pluginId}/logs/export?${params}`);
      const blob = await response.blob();
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `plugin-${pluginId}-logs.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success('Logs exported successfully');
    } catch (error) {
      toast.error('Failed to export logs');
    }
  };

  // 로그 복사
  const copyLog = (log: LogEntry) => {
    const logText = `[${log.timestamp}] ${log.level.toUpperCase()}: ${log.message}`;
    navigator.clipboard.writeText(logText);
    toast.success('Log copied to clipboard');
  };

  // 메시지 하이라이트
  const highlightMessage = (message: string, search: string) => {
    if (!highlightSearch || !search) return message;
    
    const regex = new RegExp(`(${search})`, 'gi');
    return message.replace(regex, '<mark class="bg-yellow-200">$1</mark>');
  };

  // 로그 레벨 아이콘
  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'error':
        return <XCircle className="h-4 w-4" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4" />;
      case 'info':
        return <Info className="h-4 w-4" />;
      case 'debug':
        return <CheckCircle className="h-4 w-4" />;
      default:
        return <Circle className="h-4 w-4" />;
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Toolbar */}
      {showToolbar && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={loadLogs}
              disabled={isLoading}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              Refresh
            </Button>

            {realTime && (
              <Button
                variant={isStreaming ? "destructive" : "default"}
                size="sm"
                onClick={isStreaming ? stopStreaming : startStreaming}
              >
                {isStreaming ? (
                  <>
                    <Square className="h-4 w-4 mr-1" />
                    Stop Stream
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-1" />
                    Start Stream
                  </>
                )}
              </Button>
            )}

            <div className="flex items-center gap-2">
              <Switch
                checked={autoScrollEnabled}
                onCheckedChange={setAutoScrollEnabled}
              />
              <Label className="text-sm">Auto Scroll</Label>
            </div>

            <Badge variant="outline">
              {filteredLogs.length} / {logs.length} logs
            </Badge>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? (
                <Minimize2 className="h-4 w-4" />
              ) : (
                <Maximize2 className="h-4 w-4" />
              )}
            </Button>

            {exportable && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-1" />
                    Export
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem onClick={() => exportLogs('csv')}>
                    Export as CSV
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => exportLogs('json')}>
                    Export as JSON
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => exportLogs('txt')}>
                    Export as Text
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </div>
      )}

      {/* Filters */}
      {showFilters && (
        <Card>
          <CardContent className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Search */}
              {searchable && (
                <div>
                  <Label htmlFor="log-search">Search</Label>
                  <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="log-search"
                      placeholder="Search logs..."
                      value={filters.search}
                      onChange={(e) => updateFilter('search', e.target.value)}
                      className="pl-8"
                    />
                  </div>
                </div>
              )}

              {/* Level Filter */}
              <div>
                <Label>Log Levels</Label>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" className="w-full justify-between">
                      <span>{filters.level.length} selected</span>
                      <ChevronDown className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent className="w-56">
                    {LOG_LEVELS.map((level) => (
                      <DropdownMenuCheckboxItem
                        key={level.value}
                        checked={filters.level.includes(level.value)}
                        onCheckedChange={(checked) => {
                          const newLevels = checked
                            ? [...filters.level, level.value]
                            : filters.level.filter(l => l !== level.value);
                          updateFilter('level', newLevels);
                        }}
                      >
                        <div className="flex items-center gap-2">
                          <div className={`w-3 h-3 rounded ${level.bg}`} />
                          {level.label}
                        </div>
                      </DropdownMenuCheckboxItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              {/* Time Range */}
              <div>
                <Label>Time Range</Label>
                <Select
                  value={filters.timeRange}
                  onValueChange={(value) => updateFilter('timeRange', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="15m">Last 15 minutes</SelectItem>
                    <SelectItem value="1h">Last hour</SelectItem>
                    <SelectItem value="6h">Last 6 hours</SelectItem>
                    <SelectItem value="24h">Last 24 hours</SelectItem>
                    <SelectItem value="7d">Last 7 days</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Execution ID */}
              <div>
                <Label htmlFor="execution-id">Execution ID</Label>
                <Input
                  id="execution-id"
                  placeholder="Filter by execution..."
                  value={filters.execution_id}
                  onChange={(e) => updateFilter('execution_id', e.target.value)}
                />
              </div>
            </div>

            <div className="flex items-center gap-4 mt-4">
              <div className="flex items-center gap-2">
                <Switch
                  checked={showContext}
                  onCheckedChange={setShowContext}
                />
                <Label className="text-sm">Show Context</Label>
              </div>

              <div className="flex items-center gap-2">
                <Switch
                  checked={highlightSearch}
                  onCheckedChange={setHighlightSearch}
                />
                <Label className="text-sm">Highlight Search</Label>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Log Viewer */}
      <Card className={isExpanded ? 'fixed inset-4 z-50' : ''}>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <Terminal className="h-5 w-5" />
            Execution Logs
            {isStreaming && (
              <Badge variant="secondary" className="animate-pulse">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-1" />
                Live
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea
            ref={scrollAreaRef}
            className="font-mono text-sm"
            style={{ height: isExpanded ? 'calc(100vh - 200px)' : height }}
          >
            <div className="p-4 space-y-1">
              {filteredLogs.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  {isLoading ? 'Loading logs...' : 'No logs found'}
                </div>
              ) : (
                filteredLogs.map((log) => {
                  const levelConfig = LOG_LEVELS.find(l => l.value === log.level);
                  
                  return (
                    <div
                      key={log.id}
                      className={`p-2 rounded-sm border-l-4 hover:bg-muted/50 cursor-pointer ${
                        levelConfig?.bg || 'bg-muted'
                      } ${
                        log.level === 'error' ? 'border-l-red-500' :
                        log.level === 'warning' ? 'border-l-yellow-500' :
                        log.level === 'info' ? 'border-l-blue-500' :
                        'border-l-gray-300'
                      }`}
                      onClick={() => setSelectedLog(log)}
                    >
                      <div className="flex items-start gap-2">
                        <span className="text-muted-foreground text-xs whitespace-nowrap">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                        
                        <div className={`flex items-center gap-1 ${levelConfig?.color}`}>
                          {getLevelIcon(log.level)}
                          <Badge variant="outline" className="text-xs">
                            {log.level.toUpperCase()}
                          </Badge>
                        </div>

                        <div className="flex-1 min-w-0">
                          <div
                            className="break-words"
                            dangerouslySetInnerHTML={{
                              __html: highlightMessage(log.message, filters.search)
                            }}
                          />
                          
                          {showContext && log.context && (
                            <div className="mt-1 text-xs text-muted-foreground">
                              <pre className="whitespace-pre-wrap">
                                {JSON.stringify(log.context, null, 2)}
                              </pre>
                            </div>
                          )}
                          
                          {log.execution_id && (
                            <div className="text-xs text-muted-foreground mt-1">
                              Execution: {log.execution_id}
                            </div>
                          )}
                        </div>

                        <div className="flex items-center gap-1">
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 w-6 p-0"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    copyLog(log);
                                  }}
                                >
                                  <Copy className="h-3 w-3" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Copy log</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Log Detail Dialog */}
      <Dialog open={!!selectedLog} onOpenChange={() => setSelectedLog(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Log Details
            </DialogTitle>
          </DialogHeader>
          
          {selectedLog && (
            <ScrollArea className="max-h-[60vh]">
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <Label>Timestamp</Label>
                    <div className="font-mono">
                      {new Date(selectedLog.timestamp).toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <Label>Level</Label>
                    <Badge variant="outline">{selectedLog.level.toUpperCase()}</Badge>
                  </div>
                  {selectedLog.execution_id && (
                    <div>
                      <Label>Execution ID</Label>
                      <div className="font-mono">{selectedLog.execution_id}</div>
                    </div>
                  )}
                  {selectedLog.source && (
                    <div>
                      <Label>Source</Label>
                      <div className="font-mono">{selectedLog.source}</div>
                    </div>
                  )}
                </div>

                <Separator />

                <div>
                  <Label>Message</Label>
                  <div className="mt-1 p-3 bg-muted rounded font-mono text-sm">
                    {selectedLog.message}
                  </div>
                </div>

                {selectedLog.context && (
                  <div>
                    <Label>Context</Label>
                    <pre className="mt-1 p-3 bg-muted rounded text-xs overflow-auto">
                      {JSON.stringify(selectedLog.context, null, 2)}
                    </pre>
                  </div>
                )}

                {selectedLog.stack_trace && (
                  <div>
                    <Label>Stack Trace</Label>
                    <pre className="mt-1 p-3 bg-muted rounded text-xs overflow-auto">
                      {selectedLog.stack_trace}
                    </pre>
                  </div>
                )}
              </div>
            </ScrollArea>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Circle 아이콘 컴포넌트 (lucide-react에 없는 경우)
const Circle = ({ className }: { className?: string }) => (
  <div className={`rounded-full border-2 ${className}`} />
);