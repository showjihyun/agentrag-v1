/**
 * Optimization Results Visualization Component
 * 
 * 최적화 결과를 시각적으로 표현하는 컴포넌트
 */
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Clock,
  Zap,
  Target,
  CheckCircle,
  AlertTriangle,
  Info
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

interface OptimizationResult {
  workflowId: string;
  timestamp: string;
  beforeOptimization: {
    executionTime: number;
    successRate: number;
    cost: number;
    pattern: string;
    agents: string[];
  };
  afterOptimization: {
    executionTime: number;
    successRate: number;
    cost: number;
    pattern: string;
    agents: string[];
  };
  improvements: {
    performanceImprovement: number;
    costReduction: number;
    reliabilityImprovement: number;
  };
  optimizationType: 'ml_optimization' | 'auto_tuning' | 'cost_optimization';
  confidence: number;
}

interface OptimizationTrend {
  date: string;
  avgExecutionTime: number;
  avgCost: number;
  successRate: number;
  optimizationsApplied: number;
}

interface Props {
  results: OptimizationResult[];
  trends: OptimizationTrend[];
  className?: string;
}

const COLORS = {
  performance: '#10B981',
  cost: '#F59E0B',
  reliability: '#3B82F6',
  primary: '#6366F1',
  secondary: '#8B5CF6'
};

export const OptimizationResultsVisualization: React.FC<Props> = ({
  results,
  trends,
  className = ''
}) => {
  const [selectedMetric, setSelectedMetric] = useState<'performance' | 'cost' | 'reliability'>('performance');
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');

  // 최적화 유형별 통계 계산
  const optimizationStats = React.useMemo(() => {
    const stats = {
      ml_optimization: { count: 0, avgImprovement: 0 },
      auto_tuning: { count: 0, avgImprovement: 0 },
      cost_optimization: { count: 0, avgImprovement: 0 }
    };

    results.forEach(result => {
      stats[result.optimizationType].count++;
      const improvement = selectedMetric === 'performance' 
        ? result.improvements.performanceImprovement
        : selectedMetric === 'cost'
        ? result.improvements.costReduction
        : result.improvements.reliabilityImprovement;
      
      stats[result.optimizationType].avgImprovement += improvement;
    });

    Object.keys(stats).forEach(key => {
      const typedKey = key as keyof typeof stats;
      if (stats[typedKey].count > 0) {
        stats[typedKey].avgImprovement /= stats[typedKey].count;
      }
    });

    return stats;
  }, [results, selectedMetric]);

  // 성과 분포 데이터
  const performanceDistribution = React.useMemo(() => {
    const ranges = [
      { name: '0-10%', min: 0, max: 10, count: 0 },
      { name: '10-25%', min: 10, max: 25, count: 0 },
      { name: '25-50%', min: 25, max: 50, count: 0 },
      { name: '50%+', min: 50, max: 100, count: 0 }
    ];

    results.forEach(result => {
      const improvement = result.improvements.performanceImprovement;
      const range = ranges.find(r => improvement >= r.min && improvement < r.max);
      if (range) range.count++;
    });

    return ranges;
  }, [results]);

  // 비용 절감 누적 데이터
  const cumulativeSavings = React.useMemo(() => {
    let cumulative = 0;
    return results.map((result, index) => {
      const monthlySavings = result.beforeOptimization.cost * 
        (result.improvements.costReduction / 100) * 1000; // 월 1000회 실행 가정
      cumulative += monthlySavings;
      
      return {
        index: index + 1,
        workflowName: `Workflow ${index + 1}`,
        monthlySavings,
        cumulativeSavings: cumulative
      };
    });
  }, [results]);

  const getImprovementColor = (improvement: number) => {
    if (improvement >= 30) return 'text-green-600';
    if (improvement >= 15) return 'text-blue-600';
    if (improvement >= 5) return 'text-yellow-600';
    return 'text-gray-600';
  };

  const getImprovementIcon = (improvement: number) => {
    if (improvement >= 20) return <TrendingUp className="w-4 h-4 text-green-600" />;
    if (improvement >= 10) return <Zap className="w-4 h-4 text-blue-600" />;
    if (improvement >= 5) return <Target className="w-4 h-4 text-yellow-600" />;
    return <Info className="w-4 h-4 text-gray-600" />;
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 메트릭 선택 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-semibold text-gray-900">최적화 결과 분석</h2>
          <Badge variant="outline" className="bg-blue-50 text-blue-700">
            {results.length}개 워크플로우
          </Badge>
        </div>
        
        <div className="flex items-center gap-2">
          <div className="flex bg-gray-100 rounded-lg p-1">
            {(['performance', 'cost', 'reliability'] as const).map((metric) => (
              <button
                key={metric}
                onClick={() => setSelectedMetric(metric)}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  selectedMetric === metric
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {metric === 'performance' && '성능'}
                {metric === 'cost' && '비용'}
                {metric === 'reliability' && '안정성'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 주요 지표 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">평균 성능 개선</p>
                <p className="text-2xl font-bold text-green-600">
                  {(results.reduce((sum, r) => sum + r.improvements.performanceImprovement, 0) / results.length || 0).toFixed(1)}%
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">평균 비용 절감</p>
                <p className="text-2xl font-bold text-blue-600">
                  {(results.reduce((sum, r) => sum + r.improvements.costReduction, 0) / results.length || 0).toFixed(1)}%
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">월간 절약액</p>
                <p className="text-2xl font-bold text-purple-600">
                  ${cumulativeSavings[cumulativeSavings.length - 1]?.cumulativeSavings.toFixed(0) || 0}
                </p>
              </div>
              <Target className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">평균 신뢰도</p>
                <p className="text-2xl font-bold text-orange-600">
                  {(results.reduce((sum, r) => sum + r.confidence, 0) / results.length * 100 || 0).toFixed(0)}%
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 트렌드 차트 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5" />
              성능 트렌드
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="avgExecutionTime" 
                  stroke={COLORS.performance} 
                  strokeWidth={2}
                  name="평균 실행시간 (초)"
                />
                <Line 
                  type="monotone" 
                  dataKey="successRate" 
                  stroke={COLORS.reliability} 
                  strokeWidth={2}
                  name="성공률 (%)"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="w-5 h-5" />
              비용 절감 누적
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={cumulativeSavings}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="workflowName" />
                <YAxis />
                <Tooltip formatter={(value: number) => [`$${value.toFixed(0)}`, '']} />
                <Area 
                  type="monotone" 
                  dataKey="cumulativeSavings" 
                  stroke={COLORS.cost} 
                  fill={COLORS.cost}
                  fillOpacity={0.3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* 최적화 유형별 분석 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>최적화 유형별 성과</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(optimizationStats).map(([type, stats]) => {
                const typeNames = {
                  ml_optimization: 'ML 기반 최적화',
                  auto_tuning: '자동 성능 튜닝',
                  cost_optimization: '비용 최적화'
                };
                
                return (
                  <div key={type} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900">
                        {typeNames[type as keyof typeof typeNames]}
                      </p>
                      <p className="text-sm text-gray-600">{stats.count}회 적용</p>
                    </div>
                    <div className="text-right">
                      <p className={`text-lg font-bold ${getImprovementColor(stats.avgImprovement)}`}>
                        {stats.avgImprovement.toFixed(1)}%
                      </p>
                      <div className="flex items-center gap-1">
                        {getImprovementIcon(stats.avgImprovement)}
                        <span className="text-xs text-gray-500">평균 개선</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>성능 개선 분포</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={performanceDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, count }) => `${name}: ${count}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {performanceDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={Object.values(COLORS)[index % Object.values(COLORS).length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* 개별 최적화 결과 목록 */}
      <Card>
        <CardHeader>
          <CardTitle>최근 최적화 결과</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {results.slice(0, 5).map((result, index) => (
              <motion.div
                key={result.workflowId}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="font-medium text-gray-900">
                      워크플로우 {result.workflowId}
                    </h4>
                    <Badge variant="outline" className="text-xs">
                      {result.optimizationType === 'ml_optimization' && 'ML 최적화'}
                      {result.optimizationType === 'auto_tuning' && '자동 튜닝'}
                      {result.optimizationType === 'cost_optimization' && '비용 최적화'}
                    </Badge>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">성능: </span>
                      <span className={getImprovementColor(result.improvements.performanceImprovement)}>
                        +{result.improvements.performanceImprovement.toFixed(1)}%
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">비용: </span>
                      <span className={getImprovementColor(result.improvements.costReduction)}>
                        -{result.improvements.costReduction.toFixed(1)}%
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">신뢰도: </span>
                      <span className="text-blue-600">{(result.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-xs text-gray-500 mb-1">
                    {new Date(result.timestamp).toLocaleDateString()}
                  </div>
                  <Progress 
                    value={result.confidence * 100} 
                    className="w-20 h-2"
                  />
                </div>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};