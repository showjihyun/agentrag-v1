'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Settings, 
  TrendingUp,
  Zap,
  Shield,
  Cpu,
  MemoryStick,
  HardDrive,
  Network,
  RefreshCw,
  Play,
  Pause,
  BarChart3,
  AlertCircle,
  Wrench
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, BarChart, Bar } from 'recharts';

interface SystemMetrics {
  timestamp: string;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_io: number;
  active_connections: number;
  response_time: number;
  throughput: number;
  error_rate: number;
  queue_length: number;
  agent_count: number;
  execution_success_rate: number;
}

interface AnomalyAlert {
  alert_id: string;
  anomaly_type: string;
  severity: string;
  description: string;
  affected_components: string[];
  confidence_score: number;
  timestamp: string;
}

interface MaintenanceTask {
  task_id: string;
  action: string;
  target_component: string;
  priority: string;
  estimated_duration: number;
  success_probability: number;
  status: string;
  scheduled_time?: string;
}

interface HealthReport {
  overall_status: string;
  component_status: Record<string, string>;
  active_anomalies: AnomalyAlert[];
  maintenance_recommendations: MaintenanceTask[];
  risk_assessment: Record<string, number>;
  generated_at: string;
}

interface PredictiveMaintenanceBlockProps {
  onConfigChange?: (config: any) => void;
  initialConfig?: any;
}

const PredictiveMaintenanceBlock: React.FC<PredictiveMaintenanceBlockProps> = ({
  onConfigChange,
  initialConfig = {}
}) => {
  // State
  const [healthReport, setHealthReport] = useState<HealthReport | null>(null);
  const [currentMetrics, setCurrentMetrics] = useState<SystemMetrics | null>(null);
  const [anomalies, setAnomalies] = useState<AnomalyAlert[]>([]);
  const [maintenanceTasks, setMaintenanceTasks] = useState<MaintenanceTask[]>([]);
  const [performanceTrends, setPerformanceTrends] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [config, setConfig] = useState({
    auto_healing_enabled: true,
    collection_interval: 30,
    anomaly_threshold: 0.8,
    max_concurrent_maintenance: 3,
    ...initialConfig
  });

  // Status colors
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'critical': return 'text-red-600 bg-red-100';
      case 'degraded': return 'text-orange-600 bg-orange-100';
      case 'maintenance': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'low': return 'text-blue-600 bg-blue-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'critical': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  // API calls
  const fetchSystemHealth = async () => {
    try {
      const response = await fetch('/api/agent-builder/predictive-maintenance/health');
      if (response.ok) {
        const data = await response.json();
        setHealthReport(data.health_report);
      }
    } catch (error) {
      console.error('Failed to fetch system health:', error);
    }
  };

  const fetchCurrentMetrics = async () => {
    try {
      const response = await fetch('/api/agent-builder/predictive-maintenance/metrics/current');
      if (response.ok) {
        const data = await response.json();
        setCurrentMetrics(data.metrics);
      }
    } catch (error) {
      console.error('Failed to fetch current metrics:', error);
    }
  };

  const fetchAnomalies = async () => {
    try {
      const response = await fetch('/api/agent-builder/predictive-maintenance/anomalies/detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ time_window_hours: 1 })
      });
      if (response.ok) {
        const data = await response.json();
        setAnomalies(data.anomalies);
      }
    } catch (error) {
      console.error('Failed to fetch anomalies:', error);
    }
  };

  const fetchMaintenanceSchedule = async () => {
    try {
      const response = await fetch('/api/agent-builder/predictive-maintenance/maintenance/schedule');
      if (response.ok) {
        const data = await response.json();
        setMaintenanceTasks([...data.scheduled_tasks, ...data.active_tasks]);
      }
    } catch (error) {
      console.error('Failed to fetch maintenance schedule:', error);
    }
  };

  const fetchPerformanceAnalytics = async () => {
    try {
      const response = await fetch('/api/agent-builder/predictive-maintenance/analytics');
      if (response.ok) {
        const data = await response.json();
        // Convert trends to chart data
        const chartData = data.performance_trends.cpu_usage?.map((cpu: number, index: number) => ({
          time: index,
          cpu: cpu,
          memory: data.performance_trends.memory_usage[index],
          response_time: data.performance_trends.response_time[index],
          throughput: data.performance_trends.throughput[index]
        })) || [];
        setPerformanceTrends(chartData);
      }
    } catch (error) {
      console.error('Failed to fetch performance analytics:', error);
    }
  };

  const executeMaintenanceTask = async (taskId: string) => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/agent-builder/predictive-maintenance/maintenance/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskId })
      });
      
      if (response.ok) {
        await fetchMaintenanceSchedule();
        await fetchSystemHealth();
      }
    } catch (error) {
      console.error('Failed to execute maintenance task:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateConfiguration = async () => {
    try {
      const response = await fetch('/api/agent-builder/predictive-maintenance/configuration', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      
      if (response.ok) {
        onConfigChange?.(config);
      }
    } catch (error) {
      console.error('Failed to update configuration:', error);
    }
  };

  // Effects
  useEffect(() => {
    const fetchAllData = async () => {
      setIsLoading(true);
      await Promise.all([
        fetchSystemHealth(),
        fetchCurrentMetrics(),
        fetchAnomalies(),
        fetchMaintenanceSchedule(),
        fetchPerformanceAnalytics()
      ]);
      setIsLoading(false);
    };

    fetchAllData();

    // Set up polling if monitoring is enabled
    let interval: NodeJS.Timeout;
    if (isMonitoring) {
      interval = setInterval(fetchAllData, config.collection_interval * 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isMonitoring, config.collection_interval]);

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Shield className="h-6 w-6 text-blue-600" />
            Predictive Maintenance & Self-Healing
          </h2>
          <p className="text-gray-600 mt-1">
            AI-powered system monitoring, anomaly detection, and automated maintenance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsMonitoring(!isMonitoring)}
          >
            {isMonitoring ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            {isMonitoring ? 'Pause' : 'Start'} Monitoring
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              fetchSystemHealth();
              fetchCurrentMetrics();
              fetchAnomalies();
              fetchMaintenanceSchedule();
              fetchPerformanceAnalytics();
            }}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* System Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">System Status</p>
                <p className="text-lg font-semibold">
                  {healthReport?.overall_status || 'Unknown'}
                </p>
              </div>
              <div className={`p-2 rounded-full ${getStatusColor(healthReport?.overall_status || 'unknown')}`}>
                <Activity className="h-4 w-4" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Anomalies</p>
                <p className="text-lg font-semibold">{anomalies.length}</p>
              </div>
              <div className="p-2 rounded-full bg-red-100 text-red-600">
                <AlertTriangle className="h-4 w-4" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Maintenance Tasks</p>
                <p className="text-lg font-semibold">{maintenanceTasks.length}</p>
              </div>
              <div className="p-2 rounded-full bg-blue-100 text-blue-600">
                <Wrench className="h-4 w-4" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Auto-Healing</p>
                <p className="text-lg font-semibold">
                  {config.auto_healing_enabled ? 'Enabled' : 'Disabled'}
                </p>
              </div>
              <div className={`p-2 rounded-full ${config.auto_healing_enabled ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-600'}`}>
                <Zap className="h-4 w-4" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="anomalies">Anomalies</TabsTrigger>
          <TabsTrigger value="maintenance">Maintenance</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* System Health */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  System Health
                </CardTitle>
              </CardHeader>
              <CardContent>
                {healthReport && (
                  <div className="space-y-3">
                    {Object.entries(healthReport.component_status).map(([component, status]) => (
                      <div key={component} className="flex items-center justify-between">
                        <span className="capitalize">{component.replace('_', ' ')}</span>
                        <Badge className={getStatusColor(status)}>
                          {status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Performance Trends */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Performance Trends
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={performanceTrends}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="cpu" stroke="#8884d8" strokeWidth={2} />
                      <Line type="monotone" dataKey="memory" stroke="#82ca9d" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Risk Assessment */}
          {healthReport?.risk_assessment && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5" />
                  Risk Assessment
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {Object.entries(healthReport.risk_assessment).map(([risk, score]) => (
                    <div key={risk} className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm capitalize">{risk.replace('_', ' ')}</span>
                        <span className="text-sm font-medium">{(score * 100).toFixed(1)}%</span>
                      </div>
                      <Progress value={score * 100} className="h-2" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Metrics Tab */}
        <TabsContent value="metrics" className="space-y-4">
          {currentMetrics && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Cpu className="h-8 w-8 text-blue-600" />
                    <div>
                      <p className="text-sm text-gray-600">CPU Usage</p>
                      <p className="text-xl font-bold">{currentMetrics.cpu_usage.toFixed(1)}%</p>
                      <Progress value={currentMetrics.cpu_usage} className="h-2 mt-1" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <MemoryStick className="h-8 w-8 text-green-600" />
                    <div>
                      <p className="text-sm text-gray-600">Memory Usage</p>
                      <p className="text-xl font-bold">{currentMetrics.memory_usage.toFixed(1)}%</p>
                      <Progress value={currentMetrics.memory_usage} className="h-2 mt-1" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <HardDrive className="h-8 w-8 text-orange-600" />
                    <div>
                      <p className="text-sm text-gray-600">Disk Usage</p>
                      <p className="text-xl font-bold">{currentMetrics.disk_usage.toFixed(1)}%</p>
                      <Progress value={currentMetrics.disk_usage} className="h-2 mt-1" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Network className="h-8 w-8 text-purple-600" />
                    <div>
                      <p className="text-sm text-gray-600">Network I/O</p>
                      <p className="text-xl font-bold">{currentMetrics.network_io.toFixed(1)} MB</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Clock className="h-8 w-8 text-red-600" />
                    <div>
                      <p className="text-sm text-gray-600">Response Time</p>
                      <p className="text-xl font-bold">{currentMetrics.response_time.toFixed(0)}ms</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <BarChart3 className="h-8 w-8 text-indigo-600" />
                    <div>
                      <p className="text-sm text-gray-600">Throughput</p>
                      <p className="text-xl font-bold">{currentMetrics.throughput.toFixed(0)}/min</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="h-8 w-8 text-yellow-600" />
                    <div>
                      <p className="text-sm text-gray-600">Error Rate</p>
                      <p className="text-xl font-bold">{(currentMetrics.error_rate * 100).toFixed(2)}%</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="h-8 w-8 text-green-600" />
                    <div>
                      <p className="text-sm text-gray-600">Success Rate</p>
                      <p className="text-xl font-bold">{(currentMetrics.execution_success_rate * 100).toFixed(1)}%</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Anomalies Tab */}
        <TabsContent value="anomalies" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Active Anomalies ({anomalies.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {anomalies.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
                  <p className="text-gray-600">No anomalies detected. System is running normally.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {anomalies.map((anomaly) => (
                    <Alert key={anomaly.alert_id}>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge className={getSeverityColor(anomaly.severity)}>
                                {anomaly.severity}
                              </Badge>
                              <span className="text-sm text-gray-600">
                                {new Date(anomaly.timestamp).toLocaleString()}
                              </span>
                            </div>
                            <p className="font-medium mb-1">{anomaly.description}</p>
                            <p className="text-sm text-gray-600">
                              Affected: {anomaly.affected_components.join(', ')}
                            </p>
                            <p className="text-sm text-gray-600">
                              Confidence: {(anomaly.confidence_score * 100).toFixed(1)}%
                            </p>
                          </div>
                        </div>
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Maintenance Tab */}
        <TabsContent value="maintenance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wrench className="h-5 w-5" />
                Maintenance Tasks ({maintenanceTasks.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {maintenanceTasks.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
                  <p className="text-gray-600">No maintenance tasks required.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {maintenanceTasks.map((task) => (
                    <div key={task.task_id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge variant="outline">{task.priority}</Badge>
                            <Badge variant="secondary">{task.status}</Badge>
                            <span className="text-sm text-gray-600">
                              {task.target_component}
                            </span>
                          </div>
                          <p className="font-medium mb-1 capitalize">
                            {task.action.replace('_', ' ')}
                          </p>
                          <div className="text-sm text-gray-600 space-y-1">
                            <p>Duration: {Math.round(task.estimated_duration / 60)} minutes</p>
                            <p>Success Rate: {(task.success_probability * 100).toFixed(1)}%</p>
                            {task.scheduled_time && (
                              <p>Scheduled: {new Date(task.scheduled_time).toLocaleString()}</p>
                            )}
                          </div>
                        </div>
                        <div className="flex gap-2">
                          {task.status === 'pending' && (
                            <Button
                              size="sm"
                              onClick={() => executeMaintenanceTask(task.task_id)}
                              disabled={isLoading}
                            >
                              Execute
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                System Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="auto-healing">Auto-Healing</Label>
                  <p className="text-sm text-gray-600">
                    Automatically execute maintenance tasks for critical issues
                  </p>
                </div>
                <Switch
                  id="auto-healing"
                  checked={config.auto_healing_enabled}
                  onCheckedChange={(checked) => 
                    setConfig((prev: typeof config) => ({ ...prev, auto_healing_enabled: checked }))
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="collection-interval">Collection Interval (seconds)</Label>
                <Input
                  id="collection-interval"
                  type="number"
                  value={config.collection_interval}
                  onChange={(e) => 
                    setConfig((prev: typeof config) => ({ ...prev, collection_interval: parseInt(e.target.value) }))
                  }
                  min="10"
                  max="300"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="anomaly-threshold">Anomaly Threshold</Label>
                <Input
                  id="anomaly-threshold"
                  type="number"
                  step="0.1"
                  value={config.anomaly_threshold}
                  onChange={(e) => 
                    setConfig((prev: typeof config) => ({ ...prev, anomaly_threshold: parseFloat(e.target.value) }))
                  }
                  min="0.1"
                  max="1.0"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="max-maintenance">Max Concurrent Maintenance</Label>
                <Input
                  id="max-maintenance"
                  type="number"
                  value={config.max_concurrent_maintenance}
                  onChange={(e) => 
                    setConfig((prev: typeof config) => ({ ...prev, max_concurrent_maintenance: parseInt(e.target.value) }))
                  }
                  min="1"
                  max="10"
                />
              </div>

              <Button onClick={updateConfiguration} className="w-full">
                Update Configuration
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PredictiveMaintenanceBlock;