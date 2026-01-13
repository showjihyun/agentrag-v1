/**
 * Plugin Detail Monitoring Dashboard
 * 개별 플러그인의 상세 모니터링 및 분석 대시보드
 */

'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Clock,
  Zap,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Cpu,
  Memory,
  Network,
  Database,
  Eye,
  Download,
  RefreshCw,
  Filter,
  Search,
  Calendar,
  BarChart3,
  PieChart as PieChartIcon,
  LineChart as LineChartIcon,
  Settings,
  Bell,
  BellOff,
  Loader2,
  Terminal,
  FileText,
  AlertCircle,
} from 'lucide-react';
import { toast } from 'sonner';

export interface PluginMetric {
  name: string;
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  trendValue: number;
  status: 'good' | 'warning' | 'critical';
  timestamp: string;
}

export interface PluginExecution {
  id: string;
  timestamp: string;
  duration: number;
  status: 'success' | 'error' | 'timeout';
  input_size: number;
  output_size: number;
  memory_usage: number;
  cpu_usage: number;
  error_message?: string;
  trace_id?: string;
}

export interface PluginAlert {
  id: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
  rule_id: string;
}

export interface PluginLogEntry {
  id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warning' | 'error';
  message: string;
  context?: Record<string, any>;
  execution_id?: string;
}

interface PluginDetailMonitoringProps {
  pluginId: string;
  pluginName: string;
  timeRange?: '1h' | '6h' | '24h' | '7d' | '30d';
  refreshInterval?: number;
  showComparison?: boolean;
  className?: string;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export function PluginDetailMonitoring({
  pluginId,
  pluginName,
  timeRange = '24h',
  refreshInterval = 30000,
  showComparison = false,
  className,
}: PluginDetailMonitoringProps) {
  const [metrics, setMetrics] = useState<PluginMetric[]>([]);
  const [executions, setExecutions] = useState<PluginExecution[]>([]);
  const [alerts, setAlerts] = useState<PluginAlert[]>([]);
  const [logs, setLogs] = useState<PluginLogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange);
  const [activeTab, setActiveTab] = useState('overview');
  const [logFilter, setLogFilter] = useState({
    level: 'all',
    search: '',
    execution_id: '',
  });
  const [alertsEnabled, setAlertsEnabled] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // 데이터 로딩
  const loadData = async () => {
    setIsLoading(true);
    try {
      const [metricsRes, executionsRes, alertsRes, logsRes] = await Promise.all([
        fetch(`/api/agent-builder/plugins/${pluginId}/metrics?timeRange=${selectedTimeRange}`),
        fetch(`/api/agent-builder/plugins/${pluginId}/executions?timeRange=${selectedTimeRange}&limit=100`),
        fetch(`/api/agent-builder/plugins/${pluginId}/alerts?timeRange=${selectedTimeRange}`),
        fetch(`/api/agent-builder/plugins/${pluginId}/logs?timeRange=${selectedTimeRange}&limit=500`),
      ]);

      const [metricsData, executionsData, alertsData, logsData] = await Promise.all([
        metricsRes.json(),
        executionsRes.json(),
        alertsRes.json(),
        logsRes.json(),
      ]);

      setMetrics(metricsData);
      setExecutions(executionsData);
      setAlerts(alertsData);
      setLogs(logsData);
    } catch (error) {
      toast.error('Failed to load plugin monitoring data');
      console.error('Load data error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 자동 새로고침
  useEffect(() => {
    loadData();
    
    if (autoRefresh) {
      const interval = setInterval(loadData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [pluginId, selectedTimeRange, autoRefresh, refreshInterval]);

  // 메트릭 계산
  const calculatedMetrics = useMemo(() => {
    if (executions.length === 0) return null;

    const successCount = executions.filter(e => e.status === 'success').length;
    const errorCount = executions.filter(e => e.status === 'error').length;
    const timeoutCount = executions.filter(e => e.status === 'timeout').length;
    
    const successRate = (successCount / executions.length) * 100;
    const avgDuration = executions.reduce((sum, e) => sum + e.duration, 0) / executions.length;
    const avgMemoryUsage = executions.reduce((sum, e) => sum + e.memory_usage, 0) / executions.length;
    const avgCpuUsage = executions.reduce((sum, e) => sum + e.cpu_usage, 0) / executions.length;

    return {
      totalExecutions: executions.length,
      successCount,
      errorCount,
      timeoutCount,
      successRate,
      avgDuration,
      avgMemoryUsage,
      avgCpuUsage,
    };
  }, [executions]);

  // 시계열 데이터 준비
  const timeSeriesData = useMemo(() => {
    const hourlyData: Record<string, any> = {};
    
    executions.forEach(execution => {
      const hour = new Date(execution.timestamp).toISOString().slice(0, 13) + ':00:00';
      if (!hourlyData[hour]) {
        hourlyData[hour] = {
          timestamp: hour,
          executions: 0,
          successes: 0,
          errors: 0,
          avgDuration: 0,
          avgMemory: 0,
          avgCpu: 0,
          durations: [],
          memories: [],
          cpus: [],
        };
      }
      
      hourlyData[hour].executions++;
      if (execution.status === 'success') hourlyData[hour].successes++;
      if (execution.status === 'error') hourlyData[hour].errors++;
      
      hourlyData[hour].durations.push(execution.duration);
      hourlyData[hour].memories.push(execution.memory_usage);
      hourlyData[hour].cpus.push(execution.cpu_usage);
    });

    return Object.values(hourlyData).map((data: any) => ({
      ...data,
      avgDuration: data.durations.reduce((a: number, b: number) => a + b, 0) / data.durations.length,
      avgMemory: data.memories.reduce((a: number, b: number) => a + b, 0) / data.memories.length,
      avgCpu: data.cpus.reduce((a: number, b: number) => a + b, 0) / data.cpus.length,
      successRate: (data.successes / data.executions) * 100,
    })).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  }, [executions]);

  // 필터링된 로그
  const filteredLogs = useMemo(() => {
    return logs.filter(log => {
      if (logFilter.level !== 'all' && log.level !== logFilter.level) return false;
      if (logFilter.search && !log.message.toLowerCase().includes(logFilter.search.toLowerCase())) return false;
      if (logFilter.execution_id && log.execution_id !== logFilter.execution_id) return false;
      return true;
    });
  }, [logs, logFilter]);

  // 알림 확인
  const acknowledgeAlert = async (alertId: string) => {
    try {
      await fetch(`/api/agent-builder/plugins/${pluginId}/alerts/${alertId}/acknowledge`, {
        method: 'POST',
      });
      
      setAlerts(prev => prev.map(alert => 
        alert.id === alertId ? { ...alert, acknowledged: true } : alert
      ));
      
      toast.success('Alert acknowledged');
    } catch (error) {
      toast.error('Failed to acknowledge alert');
    }
  };

  // 데이터 내보내기
  const exportData = async (type: 'metrics' | 'executions' | 'logs') => {
    try {
      const response = await fetch(`/api/agent-builder/plugins/${pluginId}/export/${type}?timeRange=${selectedTimeRange}`);
      const blob = await response.blob();
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${pluginName}-${type}-${selectedTimeRange}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success(`${type} data exported successfully`);
    } catch (error) {
      toast.error(`Failed to export ${type} data`);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">{pluginName} Monitoring</h2>
          <p className="text-muted-foreground">Detailed performance and health metrics</p>
        </div>
        
        <div className="flex items-center gap-2">
          <Select value={selectedTimeRange} onValueChange={setSelectedTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1h">Last Hour</SelectItem>
              <SelectItem value="6h">Last 6 Hours</SelectItem>
              <SelectItem value="24h">Last 24 Hours</SelectItem>
              <SelectItem value="7d">Last 7 Days</SelectItem>
              <SelectItem value="30d">Last 30 Days</SelectItem>
            </SelectContent>
          </Select>
          
          <div className="flex items-center gap-2">
            <Switch
              checked={autoRefresh}
              onCheckedChange={setAutoRefresh}
            />
            <Label className="text-sm">Auto Refresh</Label>
          </div>
          
          <Button variant="outline" size="sm" onClick={loadData}>
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </Button>
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-1" />
                Export
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => exportData('metrics')}>
                Export Metrics
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => exportData('executions')}>
                Export Executions
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => exportData('logs')}>
                Export Logs
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Quick Stats */}
      {calculatedMetrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Executions</p>
                  <p className="text-2xl font-bold">{calculatedMetrics.totalExecutions}</p>
                </div>
                <Activity className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Success Rate</p>
                  <p className="text-2xl font-bold">{calculatedMetrics.successRate.toFixed(1)}%</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Avg Duration</p>
                  <p className="text-2xl font-bold">{calculatedMetrics.avgDuration.toFixed(0)}ms</p>
                </div>
                <Clock className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Error Count</p>
                  <p className="text-2xl font-bold">{calculatedMetrics.errorCount}</p>
                </div>
                <XCircle className="h-8 w-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Alerts */}
      {alerts.filter(a => !a.acknowledged).length > 0 && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {alerts.filter(a => !a.acknowledged).length} unacknowledged alert(s)
          </AlertDescription>
        </Alert>
      )}

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="executions">Executions</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Performance Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Execution Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={timeSeriesData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="timestamp" 
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    />
                    <YAxis />
                    <Tooltip 
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                    />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="executions" 
                      stroke="#8884d8" 
                      name="Executions"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="successes" 
                      stroke="#82ca9d" 
                      name="Successes"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="errors" 
                      stroke="#ff7c7c" 
                      name="Errors"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Success Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={timeSeriesData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="timestamp" 
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    />
                    <YAxis domain={[0, 100]} />
                    <Tooltip 
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                      formatter={(value: number) => [`${value.toFixed(1)}%`, 'Success Rate']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="successRate" 
                      stroke="#82ca9d" 
                      fill="#82ca9d" 
                      fillOpacity={0.3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Resource Usage */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Average Duration</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={timeSeriesData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="timestamp" 
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    />
                    <YAxis />
                    <Tooltip 
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                      formatter={(value: number) => [`${value.toFixed(0)}ms`, 'Duration']}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="avgDuration" 
                      stroke="#ffc658" 
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Resource Usage</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={timeSeriesData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="timestamp" 
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    />
                    <YAxis />
                    <Tooltip 
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                    />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="avgMemory" 
                      stroke="#8884d8" 
                      name="Memory (MB)"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="avgCpu" 
                      stroke="#82ca9d" 
                      name="CPU (%)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          {/* Performance metrics would go here */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Analysis</CardTitle>
              <CardDescription>
                Detailed performance metrics and optimization suggestions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Performance analysis features coming soon...
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="executions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Executions</CardTitle>
              <CardDescription>
                Latest plugin execution history
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                <div className="space-y-2">
                  {executions.slice(0, 50).map((execution) => (
                    <div
                      key={execution.id}
                      className="flex items-center justify-between p-3 border rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        {execution.status === 'success' ? (
                          <CheckCircle className="h-5 w-5 text-green-500" />
                        ) : execution.status === 'error' ? (
                          <XCircle className="h-5 w-5 text-red-500" />
                        ) : (
                          <Clock className="h-5 w-5 text-yellow-500" />
                        )}
                        <div>
                          <div className="font-medium">
                            {new Date(execution.timestamp).toLocaleString()}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Duration: {execution.duration}ms | Memory: {execution.memory_usage}MB
                          </div>
                          {execution.error_message && (
                            <div className="text-sm text-red-500">
                              {execution.error_message}
                            </div>
                          )}
                        </div>
                      </div>
                      <Badge
                        variant={
                          execution.status === 'success'
                            ? 'default'
                            : execution.status === 'error'
                            ? 'destructive'
                            : 'secondary'
                        }
                      >
                        {execution.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          {/* Log Filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <Label htmlFor="log-search">Search</Label>
                  <Input
                    id="log-search"
                    placeholder="Search logs..."
                    value={logFilter.search}
                    onChange={(e) => setLogFilter(prev => ({ ...prev, search: e.target.value }))}
                  />
                </div>
                <div>
                  <Label htmlFor="log-level">Level</Label>
                  <Select
                    value={logFilter.level}
                    onValueChange={(value) => setLogFilter(prev => ({ ...prev, level: value }))}
                  >
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      <SelectItem value="debug">Debug</SelectItem>
                      <SelectItem value="info">Info</SelectItem>
                      <SelectItem value="warning">Warning</SelectItem>
                      <SelectItem value="error">Error</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Logs */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Terminal className="h-5 w-5" />
                Logs ({filteredLogs.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                <div className="space-y-1 font-mono text-sm">
                  {filteredLogs.map((log) => (
                    <div
                      key={log.id}
                      className={`p-2 rounded ${
                        log.level === 'error'
                          ? 'bg-red-50 text-red-900'
                          : log.level === 'warning'
                          ? 'bg-yellow-50 text-yellow-900'
                          : log.level === 'info'
                          ? 'bg-blue-50 text-blue-900'
                          : 'bg-muted'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        <span className="text-muted-foreground">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                        <Badge
                          variant={
                            log.level === 'error'
                              ? 'destructive'
                              : log.level === 'warning'
                              ? 'secondary'
                              : 'outline'
                          }
                          className="text-xs"
                        >
                          {log.level.toUpperCase()}
                        </Badge>
                        <span className="flex-1">{log.message}</span>
                      </div>
                      {log.execution_id && (
                        <div className="text-xs text-muted-foreground mt-1">
                          Execution: {log.execution_id}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <div className="space-y-4">
            {alerts.map((alert) => (
              <Alert
                key={alert.id}
                variant={
                  alert.severity === 'critical' || alert.severity === 'error'
                    ? 'destructive'
                    : 'default'
                }
                className={alert.acknowledged ? 'opacity-50' : ''}
              >
                <AlertCircle className="h-4 w-4" />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">{alert.title}</div>
                      <AlertDescription>{alert.message}</AlertDescription>
                      <div className="text-xs text-muted-foreground mt-1">
                        {new Date(alert.timestamp).toLocaleString()}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          alert.severity === 'critical'
                            ? 'destructive'
                            : alert.severity === 'error'
                            ? 'destructive'
                            : alert.severity === 'warning'
                            ? 'secondary'
                            : 'outline'
                        }
                      >
                        {alert.severity}
                      </Badge>
                      {!alert.acknowledged && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => acknowledgeAlert(alert.id)}
                        >
                          Acknowledge
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </Alert>
            ))}
            
            {alerts.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No alerts for this time period
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}