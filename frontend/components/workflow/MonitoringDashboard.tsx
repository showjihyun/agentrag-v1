'use client';

import React, { useState, useEffect } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Zap,
  Database,
  RefreshCw,
  Bell,
  Settings,
  BarChart3,
  PieChart,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

// Types
interface MetricCard {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon: React.ReactNode;
  color: string;
}

interface Alert {
  id: string;
  type: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  workflowId?: string;
  createdAt: string;
  acknowledged: boolean;
}

interface DLQStats {
  pending: number;
  retrying: number;
  resolved: number;
  discarded: number;
}

interface PerformanceData {
  avgDuration: number;
  p95Duration: number;
  successRate: number;
  errorRate: number;
}

interface MonitoringDashboardProps {
  workflowId?: string;
  onAlertClick?: (alert: Alert) => void;
  onViewDetails?: (section: string) => void;
}

// Metric card component
const MetricCardComponent: React.FC<MetricCard> = ({ title, value, change, changeLabel, icon, color }) => {
  const isPositive = change !== undefined && change >= 0;
  
  return (
    <div className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
          {change !== undefined && (
            <div className={cn(
              'flex items-center gap-1 text-xs mt-1',
              isPositive ? 'text-green-600' : 'text-red-600'
            )}>
              {isPositive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
              <span>{Math.abs(change)}%</span>
              {changeLabel && <span className="text-gray-400">{changeLabel}</span>}
            </div>
          )}
        </div>
        <div className={cn('p-2 rounded-lg', color)}>
          {icon}
        </div>
      </div>
    </div>
  );
};

// Alert item component
const AlertItem: React.FC<{ alert: Alert; onClick?: () => void }> = ({ alert, onClick }) => {
  const severityConfig = {
    info: { color: 'bg-blue-100 text-blue-700 border-blue-200', icon: <Activity className="w-4 h-4" /> },
    warning: { color: 'bg-yellow-100 text-yellow-700 border-yellow-200', icon: <AlertTriangle className="w-4 h-4" /> },
    error: { color: 'bg-red-100 text-red-700 border-red-200', icon: <XCircle className="w-4 h-4" /> },
    critical: { color: 'bg-red-200 text-red-800 border-red-300', icon: <XCircle className="w-4 h-4" /> },
  };

  const config = severityConfig[alert.severity];

  return (
    <div 
      className={cn(
        'flex items-start gap-3 p-3 rounded-lg border cursor-pointer hover:shadow-sm transition-shadow',
        config.color,
        alert.acknowledged && 'opacity-60'
      )}
      onClick={onClick}
    >
      {config.icon}
      <div className="flex-1 min-w-0">
        <div className="font-medium text-sm">{alert.title}</div>
        <div className="text-xs mt-0.5 truncate">{alert.message}</div>
        <div className="text-xs mt-1 opacity-70">
          {new Date(alert.createdAt).toLocaleString()}
        </div>
      </div>
    </div>
  );
};

// Simple bar chart component
const SimpleBarChart: React.FC<{ data: { label: string; value: number; color: string }[] }> = ({ data }) => {
  const maxValue = Math.max(...data.map(d => d.value), 1);
  
  return (
    <div className="space-y-2">
      {data.map((item, index) => (
        <div key={index} className="flex items-center gap-2">
          <span className="text-xs text-gray-500 w-20 truncate">{item.label}</span>
          <div className="flex-1 bg-gray-100 rounded-full h-2">
            <div 
              className={cn('h-2 rounded-full transition-all', item.color)}
              style={{ width: `${(item.value / maxValue) * 100}%` }}
            />
          </div>
          <span className="text-xs font-medium w-12 text-right">{item.value}</span>
        </div>
      ))}
    </div>
  );
};

// Main component
export const MonitoringDashboard: React.FC<MonitoringDashboardProps> = ({
  workflowId,
  onAlertClick,
  onViewDetails,
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Mock data - replace with actual API calls
  const [metrics, setMetrics] = useState({
    totalExecutions: 1234,
    activeExecutions: 5,
    successRate: 94.5,
    avgDuration: 2.3,
    errorCount: 23,
    dlqSize: 8,
  });

  const [alerts, setAlerts] = useState<Alert[]>([
    {
      id: '1',
      type: 'high_error_rate',
      severity: 'error',
      title: '높은 오류율 감지',
      message: 'workflow-123의 오류율이 15%를 초과했습니다',
      workflowId: 'workflow-123',
      createdAt: new Date().toISOString(),
      acknowledged: false,
    },
    {
      id: '2',
      type: 'slow_execution',
      severity: 'warning',
      title: '느린 실행 감지',
      message: '평균 실행 시간이 임계값을 초과했습니다',
      createdAt: new Date(Date.now() - 3600000).toISOString(),
      acknowledged: true,
    },
  ]);

  const [dlqStats, setDlqStats] = useState<DLQStats>({
    pending: 5,
    retrying: 2,
    resolved: 45,
    discarded: 3,
  });

  const [nodePerformance, setNodePerformance] = useState([
    { label: 'AI Agent', value: 45, color: 'bg-blue-500' },
    { label: 'HTTP Request', value: 32, color: 'bg-green-500' },
    { label: 'Transform', value: 28, color: 'bg-purple-500' },
    { label: 'Database', value: 18, color: 'bg-orange-500' },
    { label: 'Condition', value: 12, color: 'bg-gray-500' },
  ]);

  // Fetch data
  const fetchData = async () => {
    setIsLoading(true);
    try {
      // Replace with actual API calls
      // const response = await fetch('/api/agent-builder/monitoring/dashboard');
      // const data = await response.json();
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to fetch monitoring data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchData, 30000); // 30초마다 갱신
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const metricCards: MetricCard[] = [
    {
      title: '총 실행',
      value: metrics.totalExecutions.toLocaleString(),
      change: 12,
      changeLabel: '지난 주 대비',
      icon: <Activity className="w-5 h-5 text-blue-600" />,
      color: 'bg-blue-100',
    },
    {
      title: '활성 실행',
      value: metrics.activeExecutions,
      icon: <Zap className="w-5 h-5 text-yellow-600" />,
      color: 'bg-yellow-100',
    },
    {
      title: '성공률',
      value: `${metrics.successRate}%`,
      change: 2.3,
      changeLabel: '지난 주 대비',
      icon: <CheckCircle className="w-5 h-5 text-green-600" />,
      color: 'bg-green-100',
    },
    {
      title: '평균 실행 시간',
      value: `${metrics.avgDuration}s`,
      change: -5,
      changeLabel: '지난 주 대비',
      icon: <Clock className="w-5 h-5 text-purple-600" />,
      color: 'bg-purple-100',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">모니터링 대시보드</h2>
          <p className="text-sm text-gray-500">
            마지막 업데이트: {lastUpdated.toLocaleTimeString()}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant={autoRefresh ? 'default' : 'outline'}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={cn('w-4 h-4 mr-1', autoRefresh && 'animate-spin')} />
            자동 갱신
          </Button>
          <Button size="sm" variant="outline" onClick={fetchData}>
            <RefreshCw className="w-4 h-4" />
          </Button>
          <Button size="sm" variant="outline" onClick={() => onViewDetails?.('settings')}>
            <Settings className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metricCards.map((card, index) => (
          <MetricCardComponent key={index} {...card} />
        ))}
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Alerts section */}
        <div className="lg:col-span-2 bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Bell className="w-5 h-5 text-orange-500" />
              <h3 className="font-semibold">활성 알림</h3>
              <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs font-medium">
                {alerts.filter(a => !a.acknowledged).length}
              </span>
            </div>
            <Button size="sm" variant="ghost" onClick={() => onViewDetails?.('alerts')}>
              전체 보기
            </Button>
          </div>
          
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {alerts.length === 0 ? (
              <div className="text-center text-gray-400 py-8">
                <CheckCircle className="w-8 h-8 mx-auto mb-2" />
                <p>활성 알림이 없습니다</p>
              </div>
            ) : (
              alerts.map(alert => (
                <AlertItem 
                  key={alert.id} 
                  alert={alert} 
                  onClick={() => onAlertClick?.(alert)}
                />
              ))
            )}
          </div>
        </div>

        {/* DLQ Stats */}
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5 text-purple-500" />
              <h3 className="font-semibold">DLQ 상태</h3>
            </div>
            <Button size="sm" variant="ghost" onClick={() => onViewDetails?.('dlq')}>
              관리
            </Button>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-2 bg-yellow-50 rounded">
              <span className="text-sm">대기중</span>
              <span className="font-bold text-yellow-700">{dlqStats.pending}</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-blue-50 rounded">
              <span className="text-sm">재시도중</span>
              <span className="font-bold text-blue-700">{dlqStats.retrying}</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-green-50 rounded">
              <span className="text-sm">해결됨</span>
              <span className="font-bold text-green-700">{dlqStats.resolved}</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
              <span className="text-sm">폐기됨</span>
              <span className="font-bold text-gray-700">{dlqStats.discarded}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Performance section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Node performance */}
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-500" />
              <h3 className="font-semibold">노드별 실행 횟수</h3>
            </div>
            <Button size="sm" variant="ghost" onClick={() => onViewDetails?.('performance')}>
              상세 분석
            </Button>
          </div>
          
          <SimpleBarChart data={nodePerformance} />
        </div>

        {/* Error distribution */}
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <PieChart className="w-5 h-5 text-red-500" />
              <h3 className="font-semibold">오류 분포</h3>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">{metrics.errorCount}</div>
              <div className="text-sm text-gray-500">총 오류</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">{dlqStats.pending + dlqStats.retrying}</div>
              <div className="text-sm text-gray-500">처리 대기</div>
            </div>
          </div>

          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">TimeoutError</span>
              <span className="font-medium">12</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">ConnectionError</span>
              <span className="font-medium">6</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">ValidationError</span>
              <span className="font-medium">5</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MonitoringDashboard;
