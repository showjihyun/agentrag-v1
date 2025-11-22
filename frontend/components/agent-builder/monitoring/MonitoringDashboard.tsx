'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Cpu,
  HardDrive,
  TrendingUp,
  XCircle,
  Bell,
  BellOff,
  RefreshCw,
} from 'lucide-react';
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
} from 'recharts';

interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  active_workflows: number;
  total_executions: number;
  success_count: number;
  error_count: number;
  error_rate: number;
  avg_execution_time: number;
  cpu_percent: number;
  memory_mb: number;
  unacknowledged_alerts: number;
  timestamp: string;
}

interface WorkflowStatus {
  workflow_id: string;
  status: string;
  current_node_id?: string;
  start_time: string;
  progress_percent: number;
  completed_nodes: number;
  failed_nodes: number;
  total_nodes: number;
  estimated_completion?: string;
}

interface Alert {
  id: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  workflow_id: string;
  timestamp: string;
  acknowledged: boolean;
}

interface ResourceHistory {
  timestamp: string;
  cpu_percent: number;
  memory_mb: number;
  active_workflows: number;
}

export function MonitoringDashboard() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [activeWorkflows, setActiveWorkflows] = useState<WorkflowStatus[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [resourceHistory, setResourceHistory] = useState<ResourceHistory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchData = async () => {
    try {
      // Fetch system health
      const healthRes = await fetch('/api/agent-builder/monitoring/health');
      const healthData = await healthRes.json();
      setHealth(healthData);

      // Fetch active workflows
      const workflowsRes = await fetch('/api/agent-builder/monitoring/workflows/active');
      const workflowsData = await workflowsRes.json();
      setActiveWorkflows(workflowsData);

      // Fetch alerts
      const alertsRes = await fetch('/api/agent-builder/monitoring/alerts?acknowledged=false');
      const alertsData = await alertsRes.json();
      setAlerts(alertsData);

      // Fetch resource history
      const historyRes = await fetch('/api/agent-builder/monitoring/resource-history?limit=50');
      const historyData = await historyRes.json();
      setResourceHistory(historyData);

      setIsLoading(false);
    } catch (error) {
      console.error('Failed to fetch monitoring data:', error);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    if (autoRefresh) {
      const interval = setInterval(fetchData, 5000); // Refresh every 5 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const acknowledgeAlert = async (alertId: string) => {
    try {
      await fetch(`/api/agent-builder/monitoring/alerts/${alertId}/acknowledge`, {
        method: 'POST',
      });
      fetchData();
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600';
      case 'degraded':
        return 'text-yellow-600';
      case 'unhealthy':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'info':
        return 'default';
      case 'warning':
        return 'secondary';
      case 'error':
        return 'destructive';
      case 'critical':
        return 'destructive';
      default:
        return 'default';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Workflow Monitoring</h1>
          <p className="text-muted-foreground">Real-time system health and performance</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? (
              <>
                <Bell className="h-4 w-4 mr-2" />
                Auto-refresh On
              </>
            ) : (
              <>
                <BellOff className="h-4 w-4 mr-2" />
                Auto-refresh Off
              </>
            )}
          </Button>
          <Button variant="outline" size="sm" onClick={fetchData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* System Health Cards */}
      {health && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Activity className="h-4 w-4" />
                System Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${getStatusColor(health.status)}`}>
                {health.status.toUpperCase()}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {health.active_workflows} active workflows
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Success Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(100 - health.error_rate).toFixed(1)}%
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {health.success_count} / {health.total_executions} executions
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Cpu className="h-4 w-4 text-blue-500" />
                CPU Usage
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{health.cpu_percent.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground mt-1">
                Memory: {health.memory_mb.toFixed(0)} MB
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-500" />
                Alerts
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{health.unacknowledged_alerts}</div>
              <p className="text-xs text-muted-foreground mt-1">Unacknowledged</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="workflows">Active Workflows</TabsTrigger>
          <TabsTrigger value="alerts">
            Alerts
            {alerts.length > 0 && (
              <Badge variant="destructive" className="ml-2">
                {alerts.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          {/* Resource Usage Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Resource Usage Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={resourceHistory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                  />
                  <Legend />
                  <Area
                    yAxisId="left"
                    type="monotone"
                    dataKey="cpu_percent"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.3}
                    name="CPU %"
                  />
                  <Area
                    yAxisId="right"
                    type="monotone"
                    dataKey="memory_mb"
                    stroke="#10b981"
                    fill="#10b981"
                    fillOpacity={0.3}
                    name="Memory (MB)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Active Workflows Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Active Workflows</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={resourceHistory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                  />
                  <Line
                    type="monotone"
                    dataKey="active_workflows"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    name="Active Workflows"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Active Workflows Tab */}
        <TabsContent value="workflows">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">
                Active Workflows ({activeWorkflows.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                <div className="space-y-3">
                  {activeWorkflows.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      No active workflows
                    </div>
                  ) : (
                    activeWorkflows.map((workflow) => (
                      <div
                        key={workflow.workflow_id}
                        className="p-4 border rounded-lg space-y-2"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Activity className="h-4 w-4 text-blue-500 animate-pulse" />
                            <span className="font-medium">{workflow.workflow_id}</span>
                          </div>
                          <Badge>{workflow.status}</Badge>
                        </div>

                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Progress</span>
                            <span className="font-medium">
                              {workflow.progress_percent.toFixed(1)}%
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-500 h-2 rounded-full transition-all"
                              style={{ width: `${workflow.progress_percent}%` }}
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-3 gap-2 text-xs">
                          <div>
                            <span className="text-muted-foreground">Completed:</span>
                            <span className="ml-1 font-medium">
                              {workflow.completed_nodes}/{workflow.total_nodes}
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Failed:</span>
                            <span className="ml-1 font-medium text-red-600">
                              {workflow.failed_nodes}
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Started:</span>
                            <span className="ml-1 font-medium">
                              {new Date(workflow.start_time).toLocaleTimeString()}
                            </span>
                          </div>
                        </div>

                        {workflow.estimated_completion && (
                          <div className="text-xs text-muted-foreground">
                            <Clock className="h-3 w-3 inline mr-1" />
                            Est. completion:{' '}
                            {new Date(workflow.estimated_completion).toLocaleTimeString()}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Alerts ({alerts.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                <div className="space-y-3">
                  {alerts.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <CheckCircle2 className="h-12 w-12 mx-auto mb-2 text-green-500" />
                      No active alerts
                    </div>
                  ) : (
                    alerts.map((alert) => (
                      <div
                        key={alert.id}
                        className="p-4 border rounded-lg space-y-2"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-2">
                            {alert.severity === 'critical' || alert.severity === 'error' ? (
                              <XCircle className="h-5 w-5 text-red-500 mt-0.5" />
                            ) : (
                              <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5" />
                            )}
                            <div>
                              <div className="font-medium">{alert.title}</div>
                              <p className="text-sm text-muted-foreground mt-1">
                                {alert.message}
                              </p>
                            </div>
                          </div>
                          <Badge variant={getSeverityColor(alert.severity) as any}>
                            {alert.severity}
                          </Badge>
                        </div>

                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>
                            {new Date(alert.timestamp).toLocaleString()}
                          </span>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => acknowledgeAlert(alert.id)}
                          >
                            Acknowledge
                          </Button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Resources Tab */}
        <TabsContent value="resources" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* CPU Usage */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">CPU Usage History</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={resourceHistory}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    />
                    <YAxis />
                    <Tooltip
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                    />
                    <Area
                      type="monotone"
                      dataKey="cpu_percent"
                      stroke="#3b82f6"
                      fill="#3b82f6"
                      fillOpacity={0.5}
                      name="CPU %"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Memory Usage */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Memory Usage History</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={resourceHistory}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    />
                    <YAxis />
                    <Tooltip
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                    />
                    <Area
                      type="monotone"
                      dataKey="memory_mb"
                      stroke="#10b981"
                      fill="#10b981"
                      fillOpacity={0.5}
                      name="Memory (MB)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
