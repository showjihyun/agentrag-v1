/**
 * Performance Analytics Dashboard
 * 오케스트레이션 성능 분석 및 최적화 제안 대시보드
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from 'recharts';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Clock,
  Zap,
  AlertTriangle,
  CheckCircle,
  Target,
  Cpu,
  Memory,
  Network,
  Database,
  Users,
  MessageSquare,
  RefreshCw,
  Download,
  Filter,
  Calendar,
  BarChart3,
  PieChart as PieChartIcon,
  LineChart as LineChartIcon
} from 'lucide-react';
import { OrchestrationTypeValue } from '@/lib/constants/orchestration';

interface PerformanceMetric {
  id: string;
  name: string;
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  trendValue: number;
  target?: number;
  status: 'good' | 'warning' | 'critical';
  timestamp: string;
}

interface ExecutionData {
  id: string;
  patternType: OrchestrationTypeValue;
  startTime: string;
  endTime: string;
  duration: number;
  status: 'completed' | 'failed' | 'timeout';
  agentCount: number;
  successRate: number;
  resourceUsage: {
    cpu: number;
    memory: number;
    network: number;
  };
  metrics: Record<string, number>;
}

interface OptimizationSuggestion {
  id: string;
  type: 'performance' | 'resource' | 'configuration' | 'architecture';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  impact: string;
  effort: string;
  implementation: string[];
}

interface PerformanceAnalyticsDashboardProps {
  patternType?: OrchestrationTypeValue;
  timeRange?: '1h' | '24h' | '7d' | '30d';
  refreshInterval?: number;
}

export const PerformanceAnalyticsDashboard: React.FC<PerformanceAnalyticsDashboardProps> = ({
  patternType,
  timeRange = '24h',
  refreshInterval = 30000
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
  const [executions, setExecutions] = useState<ExecutionData[]>([]);
  const [suggestions, setSuggestions] = useState<OptimizationSuggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange);
  const [activeTab, setActiveTab] = useState('overview');

  // Mock data generation
  useEffect(() => {
    const generateMockData = () => {
      // Generate performance metrics
      const mockMetrics: PerformanceMetric[] = [
        {
          id: 'avg_execution_time',
          name: '평균 실행 시간',
          value: 8.5,
          unit: '초',
          trend: 'down',
          trendValue: -12.5,
          target: 10,
          status: 'good',
          timestamp: new Date().toISOString()
        },
        {
          id: 'success_rate',
          name: '성공률',
          value: 94.2,
          unit: '%',
          trend: 'up',
          trendValue: 2.1,
          target: 95,
          status: 'warning',
          timestamp: new Date().toISOString()
        },
        {
          id: 'throughput',
          name: '처리량',
          value: 156,
          unit: '실행/시간',
          trend: 'up',
          trendValue: 8.3,
          target: 150,
          status: 'good',
          timestamp: new Date().toISOString()
        },
        {
          id: 'resource_efficiency',
          name: '리소스 효율성',
          value: 78.9,
          unit: '%',
          trend: 'stable',
          trendValue: 0.5,
          target: 80,
          status: 'warning',
          timestamp: new Date().toISOString()
        },
        {
          id: 'agent_utilization',
          name: 'Agent 활용률',
          value: 85.3,
          unit: '%',
          trend: 'up',
          trendValue: 5.2,
          target: 85,
          status: 'good',
          timestamp: new Date().toISOString()
        },
        {
          id: 'error_rate',
          name: '오류율',
          value: 2.8,
          unit: '%',
          trend: 'down',
          trendValue: -0.7,
          target: 5,
          status: 'good',
          timestamp: new Date().toISOString()
        }
      ];

      // Generate execution data
      const mockExecutions: ExecutionData[] = Array.from({ length: 50 }, (_, i) => ({
        id: `exec_${i}`,
        patternType: ['consensus_building', 'dynamic_routing', 'swarm_intelligence', 'event_driven', 'reflection'][i % 5] as OrchestrationTypeValue,
        startTime: new Date(Date.now() - (i * 3600000)).toISOString(),
        endTime: new Date(Date.now() - (i * 3600000) + Math.random() * 600000).toISOString(),
        duration: Math.random() * 30 + 2,
        status: Math.random() > 0.1 ? 'completed' : (Math.random() > 0.5 ? 'failed' : 'timeout'),
        agentCount: Math.floor(Math.random() * 10) + 3,
        successRate: Math.random() * 20 + 80,
        resourceUsage: {
          cpu: Math.random() * 80 + 10,
          memory: Math.random() * 70 + 20,
          network: Math.random() * 60 + 15
        },
        metrics: {
          consensus_rounds: Math.floor(Math.random() * 5) + 1,
          routing_decisions: Math.floor(Math.random() * 20) + 5,
          swarm_iterations: Math.floor(Math.random() * 30) + 10
        }
      }));

      // Generate optimization suggestions
      const mockSuggestions: OptimizationSuggestion[] = [
        {
          id: 'suggestion_1',
          type: 'performance',
          priority: 'high',
          title: '합의 라운드 수 최적화',
          description: '현재 평균 4.2라운드로 합의에 도달하고 있습니다. 초기 임계값을 조정하여 3라운드 이내로 단축할 수 있습니다.',
          impact: '실행 시간 25% 단축',
          effort: '낮음',
          implementation: [
            '합의 임계값을 0.7에서 0.65로 조정',
            '초기 투표 가중치 재조정',
            'A/B 테스트로 효과 검증'
          ]
        },
        {
          id: 'suggestion_2',
          type: 'resource',
          priority: 'medium',
          title: 'Agent 풀 크기 최적화',
          description: '현재 Agent 활용률이 85%로 높습니다. 피크 시간대 성능 향상을 위해 풀 크기를 확장하는 것을 권장합니다.',
          impact: '처리량 15% 향상',
          effort: '중간',
          implementation: [
            'Agent 풀 크기를 20% 확장',
            '동적 스케일링 정책 구현',
            '리소스 모니터링 강화'
          ]
        },
        {
          id: 'suggestion_3',
          type: 'configuration',
          priority: 'low',
          title: '캐시 전략 개선',
          description: '반복적인 작업에 대한 캐시 히트율이 낮습니다. 캐시 키 전략을 개선하여 성능을 향상시킬 수 있습니다.',
          impact: '응답 시간 10% 단축',
          effort: '낮음',
          implementation: [
            '캐시 키 구조 재설계',
            'TTL 정책 최적화',
            '캐시 워밍 전략 구현'
          ]
        }
      ];

      setMetrics(mockMetrics);
      setExecutions(mockExecutions);
      setSuggestions(mockSuggestions);
      setLoading(false);
    };

    generateMockData();
    const interval = setInterval(generateMockData, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval, selectedTimeRange]);

  // Computed data for charts
  const chartData = useMemo(() => {
    const timeSeriesData = executions.slice(0, 24).reverse().map((exec, index) => ({
      time: new Date(exec.startTime).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
      duration: exec.duration,
      successRate: exec.successRate,
      agentCount: exec.agentCount,
      cpu: exec.resourceUsage.cpu,
      memory: exec.resourceUsage.memory,
      network: exec.resourceUsage.network
    }));

    const patternDistribution = executions.reduce((acc, exec) => {
      acc[exec.patternType] = (acc[exec.patternType] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const patternChartData = Object.entries(patternDistribution).map(([pattern, count]) => ({
      name: pattern.replace('_', ' '),
      value: count,
      percentage: (count / executions.length * 100).toFixed(1)
    }));

    return { timeSeriesData, patternChartData };
  }, [executions]);

  const getMetricStatusColor = (status: string) => {
    switch (status) {
      case 'good': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getTrendIcon = (trend: string, trendValue: number) => {
    if (trend === 'up') return <TrendingUp className="h-4 w-4 text-green-600" />;
    if (trend === 'down') return <TrendingDown className="h-4 w-4 text-red-600" />;
    return <Activity className="h-4 w-4 text-gray-600" />;
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2 text-lg">성능 데이터 로딩 중...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">성능 분석 대시보드</h2>
          <p className="text-gray-600">오케스트레이션 성능 메트릭 및 최적화 제안</p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-1" />
            필터
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-1" />
            내보내기
          </Button>
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-1" />
            새로고침
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">개요</TabsTrigger>
          <TabsTrigger value="performance">성능</TabsTrigger>
          <TabsTrigger value="resources">리소스</TabsTrigger>
          <TabsTrigger value="optimization">최적화</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {metrics.map((metric) => (
              <Card key={metric.id}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">{metric.name}</p>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className={`text-2xl font-bold ${getMetricStatusColor(metric.status)}`}>
                          {metric.value}{metric.unit}
                        </span>
                        {getTrendIcon(metric.trend, metric.trendValue)}
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {metric.trend === 'up' ? '+' : metric.trend === 'down' ? '' : '±'}{metric.trendValue}% 지난 기간 대비
                      </p>
                    </div>
                    
                    {metric.target && (
                      <div className="text-right">
                        <p className="text-xs text-gray-500">목표</p>
                        <p className="text-sm font-medium">{metric.target}{metric.unit}</p>
                        <Progress 
                          value={(metric.value / metric.target) * 100} 
                          className="w-16 h-2 mt-1"
                        />
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Execution Timeline */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <LineChartIcon className="h-5 w-5 mr-2" />
                실행 시간 추이
              </CardTitle>
              <CardDescription>최근 24시간 실행 시간 및 성공률 변화</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData.timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Line 
                    yAxisId="left"
                    type="monotone" 
                    dataKey="duration" 
                    stroke="#3B82F6" 
                    strokeWidth={2}
                    name="실행 시간 (초)"
                  />
                  <Line 
                    yAxisId="right"
                    type="monotone" 
                    dataKey="successRate" 
                    stroke="#10B981" 
                    strokeWidth={2}
                    name="성공률 (%)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Pattern Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <PieChartIcon className="h-5 w-5 mr-2" />
                  패턴별 사용 분포
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={chartData.patternChartData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percentage }) => `${name} (${percentage}%)`}
                    >
                      {chartData.patternChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>최근 실행 상태</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {executions.slice(0, 8).map((execution) => (
                    <div key={execution.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className={`w-3 h-3 rounded-full ${
                          execution.status === 'completed' ? 'bg-green-500' :
                          execution.status === 'failed' ? 'bg-red-500' : 'bg-yellow-500'
                        }`} />
                        <div>
                          <p className="text-sm font-medium">{execution.patternType.replace('_', ' ')}</p>
                          <p className="text-xs text-gray-500">
                            {new Date(execution.startTime).toLocaleString('ko-KR')}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium">{execution.duration.toFixed(1)}초</p>
                        <p className="text-xs text-gray-500">{execution.agentCount}개 Agent</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          {/* Performance Trends */}
          <Card>
            <CardHeader>
              <CardTitle>성능 트렌드 분석</CardTitle>
              <CardDescription>시간대별 성능 메트릭 변화</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={chartData.timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Area 
                    type="monotone" 
                    dataKey="duration" 
                    stackId="1"
                    stroke="#3B82F6" 
                    fill="#3B82F6"
                    fillOpacity={0.6}
                    name="실행 시간"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="agentCount" 
                    stackId="2"
                    stroke="#10B981" 
                    fill="#10B981"
                    fillOpacity={0.6}
                    name="Agent 수"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Performance Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>패턴별 성능 비교</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData.patternChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3B82F6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>성능 지표 요약</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">평균 응답 시간</span>
                    <span className="font-medium">8.5초</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">95th 백분위수</span>
                    <span className="font-medium">15.2초</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">99th 백분위수</span>
                    <span className="font-medium">28.7초</span>
                  </div>
                  <Separator />
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">처리량 (시간당)</span>
                    <span className="font-medium">156 실행</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">오류율</span>
                    <span className="font-medium text-red-600">2.8%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">가용성</span>
                    <span className="font-medium text-green-600">99.2%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="resources" className="space-y-6">
          {/* Resource Usage */}
          <Card>
            <CardHeader>
              <CardTitle>리소스 사용량 추이</CardTitle>
              <CardDescription>CPU, 메모리, 네트워크 사용량 변화</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData.timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="cpu" stroke="#EF4444" strokeWidth={2} name="CPU (%)" />
                  <Line type="monotone" dataKey="memory" stroke="#3B82F6" strokeWidth={2} name="메모리 (%)" />
                  <Line type="monotone" dataKey="network" stroke="#10B981" strokeWidth={2} name="네트워크 (%)" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Resource Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Cpu className="h-8 w-8 text-red-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-600">CPU 사용률</p>
                    <p className="text-2xl font-bold">45.2%</p>
                    <Progress value={45.2} className="w-full h-2 mt-2" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Memory className="h-8 w-8 text-blue-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-600">메모리 사용률</p>
                    <p className="text-2xl font-bold">62.8%</p>
                    <Progress value={62.8} className="w-full h-2 mt-2" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Network className="h-8 w-8 text-green-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-600">네트워크 I/O</p>
                    <p className="text-2xl font-bold">28.5%</p>
                    <Progress value={28.5} className="w-full h-2 mt-2" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="optimization" className="space-y-6">
          {/* Optimization Suggestions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Target className="h-5 w-5 mr-2" />
                최적화 제안
              </CardTitle>
              <CardDescription>성능 향상을 위한 맞춤형 제안사항</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {suggestions.map((suggestion) => (
                  <div key={suggestion.id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        <Badge className={getPriorityColor(suggestion.priority)}>
                          {suggestion.priority === 'high' ? '높음' : 
                           suggestion.priority === 'medium' ? '중간' : '낮음'}
                        </Badge>
                        <Badge variant="outline">{suggestion.type}</Badge>
                      </div>
                      <Button variant="outline" size="sm">
                        적용하기
                      </Button>
                    </div>
                    
                    <h4 className="font-semibold text-lg mb-2">{suggestion.title}</h4>
                    <p className="text-gray-600 mb-3">{suggestion.description}</p>
                    
                    <div className="grid grid-cols-2 gap-4 mb-3">
                      <div>
                        <p className="text-sm font-medium text-green-600">예상 효과</p>
                        <p className="text-sm">{suggestion.impact}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-blue-600">구현 난이도</p>
                        <p className="text-sm">{suggestion.effort}</p>
                      </div>
                    </div>
                    
                    <div>
                      <p className="text-sm font-medium mb-2">구현 단계</p>
                      <ul className="text-sm text-gray-600 space-y-1">
                        {suggestion.implementation.map((step, index) => (
                          <li key={index} className="flex items-center space-x-2">
                            <span className="w-4 h-4 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs">
                              {index + 1}
                            </span>
                            <span>{step}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};