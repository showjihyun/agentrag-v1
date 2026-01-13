/**
 * Performance Dashboard Component
 * 실시간 성능 모니터링 대시보드
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Cpu,
  Database,
  HardDrive,
  MemoryStick,
  Network,
  RefreshCw,
  TrendingUp,
  Users,
  Zap,
  AlertCircle,
  Info,
  XCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar
} from 'recharts';

interface MetricPoint {
  timestamp: number;
  value: number;
  labels?: Record<string, string>;
}

interface SystemMetrics {
  cpu_percent: MetricPoint[];
  memory_percent: MetricPoint[];
  disk_usage_percent: MetricPoint[];
}

interface OrchestrationMetrics {
  total_executions: MetricPoint[];
  success_rate: MetricPoint[];
  average_execution_time: MetricPoint[];
  cache_hit_rate: MetricPoint[];
}

interface Alert {
  id: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  timestamp: number;
  metric_name: string;
  current_value: number;
  threshold_value: number;
  resolved: boolean;
  resolved_at?: number;
}

interface DashboardData {
  system_metrics: SystemMetrics;
  orchestration_metrics: OrchestrationMetrics;
  current_status: {
    orchestration: {
      total_executions: number;
      successful_executions: number;
      failed_executions: number;
      current_active_executions: number;
      cache_hit_rate: number;
      pattern_usage: Record<string, number>;
    };
    system: {
      cpu_percent: number;
      memory_percent: number;
      active_executions: number;
    };
  };
  alerts: Alert[];
}

interface PerformanceDashboardProps {
  refreshInterval?: number; // milliseconds
  autoRefresh?: boolean;
}

export const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({
  refreshInterval = 30000, // 30초
  autoRefresh = true
}) => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDuration, setSelectedDuration] = useState('60'); // minutes
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // 대시보드 데이터 조회
  const fetchDashboardData = async () => {
    try {
      setError(null);
      const response = await fetch(`/api/monitoring/dashboard?duration_minutes=${selectedDuration}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        setDashboardData(result.data);
        setLastUpdated(new Date());
      } else {
        throw new Error(result.message || 'Failed to fetch dashboard data');
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  // 초기 로드 및 자동 새로고침
  useEffect(() => {
    fetchDashboardData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchDashboardData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [selectedDuration, autoRefresh, refreshInterval]);

  // 수동 새로고침
  const handleRefresh = () => {
    setLoading(true);
    fetchDashboardData();
  };

  // 메트릭 데이터를 차트 형식으로 변환
  const formatChartData = (points: MetricPoint[]) => {
    return points.map(point => ({
      timestamp: new Date(point.timestamp * 1000).toLocaleTimeString(),
      value: point.value,
      fullTimestamp: point.timestamp
    }));
  };

  // 알림 레벨별 색상
  const getAlertColor = (level: string) => {
    switch (level) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'error': return 'text-red-500 bg-red-50 border-red-200';
      case 'warning': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'info': return 'text-blue-600 bg-blue-50 border-blue-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  // 알림 아이콘
  const getAlertIcon = (level: string) => {
    switch (level) {
      case 'critical': return <XCircle className="w-4 h-4" />;
      case 'error': return <AlertCircle className="w-4 h-4" />;
      case 'warning': return <AlertTriangle className="w-4 h-4" />;
      case 'info': return <Info className="w-4 h-4" />;
      default: return <Info className="w-4 h-4" />;
    }
  };

  // 성능 상태 색상
  const getPerformanceColor = (value: number, thresholds: { warning: number; critical: number }) => {
    if (value >= thresholds.critical) return 'text-red-600';
    if (value >= thresholds.warning) return 'text-yellow-600';
    return 'text-green-600';
  };

  if (loading && !dashboardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-2">
          <RefreshCw className="w-5 h-5 animate-spin" />
          <span>대시보드 데이터를 로드하는 중...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="w-5 h-5" />
            <span>오류: {error}</span>
          </div>
          <Button onClick={handleRefresh} className="mt-4" variant="outline">
            다시 시도
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!dashboardData) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-gray-500">
            대시보드 데이터가 없습니다.
          </div>
        </CardContent>
      </Card>
    );
  }

  const { system_metrics, orchestration_metrics, current_status, alerts } = dashboardData;

  // 패턴 사용량 차트 데이터
  const patternUsageData = Object.entries(current_status.orchestration.pattern_usage).map(([pattern, count]) => ({
    name: pattern,
    value: count
  }));

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">성능 모니터링 대시보드</h1>
          <p className="text-gray-600">
            실시간 시스템 및 오케스트레이션 성능 모니터링
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <Select value={selectedDuration} onValueChange={setSelectedDuration}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="15">15분</SelectItem>
              <SelectItem value="30">30분</SelectItem>
              <SelectItem value="60">1시간</SelectItem>
              <SelectItem value="180">3시간</SelectItem>
              <SelectItem value="360">6시간</SelectItem>
              <SelectItem value="720">12시간</SelectItem>
              <SelectItem value="1440">24시간</SelectItem>
            </SelectContent>
          </Select>
          
          <Button onClick={handleRefresh} disabled={loading} variant="outline">
            <RefreshCw className={cn("w-4 h-4 mr-2", loading && "animate-spin")} />
            새로고침
          </Button>
        </div>
      </div>

      {/* 마지막 업데이트 시간 */}
      {lastUpdated && (
        <div className="text-sm text-gray-500">
          마지막 업데이트: {lastUpdated.toLocaleString()}
        </div>
      )}

      {/* 활성 알림 */}
      {alerts.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-800">
              <AlertTriangle className="w-5 h-5" />
              활성 알림 ({alerts.length}개)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {alerts.slice(0, 3).map((alert) => (
                <div key={alert.id} className={cn("p-3 rounded-lg border", getAlertColor(alert.level))}>
                  <div className="flex items-center gap-2">
                    {getAlertIcon(alert.level)}
                    <span className="font-medium">{alert.title}</span>
                    <Badge variant="outline">{alert.level}</Badge>
                  </div>
                  <p className="text-sm mt-1">{alert.message}</p>
                </div>
              ))}
              {alerts.length > 3 && (
                <div className="text-sm text-gray-600">
                  그 외 {alerts.length - 3}개의 알림이 더 있습니다.
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 현재 상태 요약 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">CPU 사용률</p>
                <p className={cn("text-2xl font-bold", getPerformanceColor(current_status.system.cpu_percent, { warning: 70, critical: 85 }))}>
                  {current_status.system.cpu_percent.toFixed(1)}%
                </p>
              </div>
              <Cpu className="w-8 h-8 text-blue-600" />
            </div>
            <Progress value={current_status.system.cpu_percent} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">메모리 사용률</p>
                <p className={cn("text-2xl font-bold", getPerformanceColor(current_status.system.memory_percent, { warning: 75, critical: 90 }))}>
                  {current_status.system.memory_percent.toFixed(1)}%
                </p>
              </div>
              <MemoryStick className="w-8 h-8 text-green-600" />
            </div>
            <Progress value={current_status.system.memory_percent} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">활성 실행</p>
                <p className="text-2xl font-bold text-purple-600">
                  {current_status.orchestration.current_active_executions}
                </p>
              </div>
              <Activity className="w-8 h-8 text-purple-600" />
            </div>
            <p className="text-sm text-gray-500 mt-2">
              총 {current_status.orchestration.total_executions}회 실행
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">캐시 히트율</p>
                <p className="text-2xl font-bold text-orange-600">
                  {(current_status.orchestration.cache_hit_rate * 100).toFixed(1)}%
                </p>
              </div>
              <Database className="w-8 h-8 text-orange-600" />
            </div>
            <Progress value={current_status.orchestration.cache_hit_rate * 100} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      {/* 상세 메트릭 탭 */}
      <Tabs defaultValue="system" className="space-y-4">
        <TabsList>
          <TabsTrigger value="system">시스템 메트릭</TabsTrigger>
          <TabsTrigger value="orchestration">오케스트레이션 메트릭</TabsTrigger>
          <TabsTrigger value="patterns">패턴 사용량</TabsTrigger>
        </TabsList>

        <TabsContent value="system" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="w-5 h-5" />
                  CPU 사용률
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={formatChartData(system_metrics.cpu_percent)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip formatter={(value) => [`${Number(value).toFixed(1)}%`, 'CPU 사용률']} />
                    <Line type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MemoryStick className="w-5 h-5" />
                  메모리 사용률
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={formatChartData(system_metrics.memory_percent)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip formatter={(value) => [`${Number(value).toFixed(1)}%`, '메모리 사용률']} />
                    <Area type="monotone" dataKey="value" stroke="#10B981" fill="#10B981" fillOpacity={0.3} />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="orchestration" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  성공률
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={formatChartData(orchestration_metrics.success_rate)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis domain={[0, 1]} tickFormatter={(value) => `${(value * 100).toFixed(0)}%`} />
                    <Tooltip formatter={(value) => [`${(Number(value) * 100).toFixed(1)}%`, '성공률']} />
                    <Line type="monotone" dataKey="value" stroke="#059669" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  평균 실행 시간
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={formatChartData(orchestration_metrics.average_execution_time)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip formatter={(value) => [`${Number(value).toFixed(2)}초`, '평균 실행 시간']} />
                    <Area type="monotone" dataKey="value" stroke="#F59E0B" fill="#F59E0B" fillOpacity={0.3} />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="w-5 h-5" />
                  캐시 히트율
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={formatChartData(orchestration_metrics.cache_hit_rate)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis domain={[0, 1]} tickFormatter={(value) => `${(value * 100).toFixed(0)}%`} />
                    <Tooltip formatter={(value) => [`${(Number(value) * 100).toFixed(1)}%`, '캐시 히트율']} />
                    <Line type="monotone" dataKey="value" stroke="#8B5CF6" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="w-5 h-5" />
                  총 실행 수
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={formatChartData(orchestration_metrics.total_executions)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip formatter={(value) => [`${Number(value)}회`, '총 실행 수']} />
                    <Bar dataKey="value" fill="#EF4444" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="patterns" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  패턴별 사용량
                </CardTitle>
                <CardDescription>
                  각 오케스트레이션 패턴의 사용 빈도
                </CardDescription>
              </CardHeader>
              <CardContent>
                {patternUsageData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={patternUsageData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {patternUsageData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-64 text-gray-500">
                    패턴 사용 데이터가 없습니다
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>패턴 사용 통계</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {patternUsageData.map((pattern, index) => (
                    <div key={pattern.name} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        />
                        <span className="font-medium">{pattern.name}</span>
                      </div>
                      <Badge variant="outline">{pattern.value}회</Badge>
                    </div>
                  ))}
                  
                  {patternUsageData.length === 0 && (
                    <div className="text-center text-gray-500 py-8">
                      아직 실행된 패턴이 없습니다
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};