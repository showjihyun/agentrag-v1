/**
 * Optimization Dashboard Component
 * 
 * AI 기반 오케스트레이션 최적화 대시보드
 */
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  DollarSign,
  Zap,
  Target,
  Settings,
  Play,
  Pause,
  BarChart3,
  PieChart,
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Cpu,
  Database
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface OptimizationMetrics {
  totalWorkflows: number;
  optimizedWorkflows: number;
  avgPerformanceImprovement: number;
  avgCostReduction: number;
  totalMonthlySavings: number;
  autoTuningEnabled: boolean;
}

interface OptimizationRecommendation {
  workflowId: string;
  workflowName: string;
  currentPattern: string;
  recommendedPattern: string;
  estimatedImprovement: {
    performance: number;
    cost: number;
    reliability: number;
  };
  priority: 'high' | 'medium' | 'low';
  autoApplicable: boolean;
  confidence: number;
}

interface CostBreakdown {
  compute: number;
  llmApi: number;
  storage: number;
  network: number;
  overhead: number;
}

export const OptimizationDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<OptimizationMetrics>({
    totalWorkflows: 0,
    optimizedWorkflows: 0,
    avgPerformanceImprovement: 0,
    avgCostReduction: 0,
    totalMonthlySavings: 0,
    autoTuningEnabled: false
  });

  const [recommendations, setRecommendations] = useState<OptimizationRecommendation[]>([]);
  const [costBreakdown, setCostBreakdown] = useState<CostBreakdown>({
    compute: 0,
    llmApi: 0,
    storage: 0,
    network: 0,
    overhead: 0
  });

  const [selectedWorkflow, setSelectedWorkflow] = useState<string>('');
  const [optimizationStrategy, setOptimizationStrategy] = useState<string>('balanced');
  const [isLoading, setIsLoading] = useState(false);
  const [autoTuningStatus, setAutoTuningStatus] = useState<'stopped' | 'running'>('stopped');

  // 데이터 로드
  useEffect(() => {
    loadOptimizationMetrics();
    loadRecommendations();
    loadCostBreakdown();
  }, []);

  const loadOptimizationMetrics = async () => {
    try {
      const response = await fetch('/api/v1/agent-plugins/optimization/recommendations');
      if (response.ok) {
        const data = await response.json();
        setMetrics({
          totalWorkflows: data.summary?.total_recommendations || 0,
          optimizedWorkflows: Math.floor((data.summary?.auto_applicable_rate || 0) / 100 * (data.summary?.total_recommendations || 0)),
          avgPerformanceImprovement: data.summary?.avg_performance_improvement || 0,
          avgCostReduction: data.summary?.avg_cost_reduction || 0,
          totalMonthlySavings: 1250, // 예시 데이터
          autoTuningEnabled: data.tuning_config?.auto_apply || false
        });
      }
    } catch (error) {
      console.error('Failed to load optimization metrics:', error);
    }
  };

  const loadRecommendations = async () => {
    try {
      // 시뮬레이션 데이터
      const mockRecommendations: OptimizationRecommendation[] = [
        {
          workflowId: 'workflow_1',
          workflowName: '문서 검색 및 분석',
          currentPattern: 'sequential',
          recommendedPattern: 'parallel',
          estimatedImprovement: {
            performance: 35,
            cost: 15,
            reliability: 5
          },
          priority: 'high',
          autoApplicable: true,
          confidence: 0.85
        },
        {
          workflowId: 'workflow_2',
          workflowName: '데이터 처리 파이프라인',
          currentPattern: 'parallel',
          recommendedPattern: 'dynamic_routing',
          estimatedImprovement: {
            performance: 20,
            cost: 25,
            reliability: 10
          },
          priority: 'medium',
          autoApplicable: false,
          confidence: 0.72
        },
        {
          workflowId: 'workflow_3',
          workflowName: '고객 지원 자동화',
          currentPattern: 'consensus',
          recommendedPattern: 'sequential',
          estimatedImprovement: {
            performance: 10,
            cost: 30,
            reliability: -5
          },
          priority: 'low',
          autoApplicable: true,
          confidence: 0.68
        }
      ];
      
      setRecommendations(mockRecommendations);
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    }
  };

  const loadCostBreakdown = async () => {
    try {
      // 시뮬레이션 데이터
      setCostBreakdown({
        compute: 45,
        llmApi: 35,
        storage: 8,
        network: 7,
        overhead: 5
      });
    } catch (error) {
      console.error('Failed to load cost breakdown:', error);
    }
  };

  const handleAutoTuningToggle = async () => {
    try {
      setIsLoading(true);
      
      if (autoTuningStatus === 'stopped') {
        const response = await fetch('/api/v1/agent-plugins/optimization/auto-tune', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            strategy: optimizationStrategy,
            auto_apply: false,
            interval_hours: 24
          })
        });
        
        if (response.ok) {
          setAutoTuningStatus('running');
        }
      } else {
        // 중지 로직 (실제로는 API 호출)
        setAutoTuningStatus('stopped');
      }
    } catch (error) {
      console.error('Failed to toggle auto tuning:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplyRecommendation = async (recommendation: OptimizationRecommendation) => {
    try {
      setIsLoading(true);
      
      // 추천 적용 API 호출 (시뮬레이션)
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // 성공 후 데이터 새로고침
      await loadOptimizationMetrics();
      await loadRecommendations();
      
    } catch (error) {
      console.error('Failed to apply recommendation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-700 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-700 border-green-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="p-6 space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI 최적화 대시보드</h1>
          <p className="text-gray-600">워크플로우 성능 및 비용 최적화 관리</p>
        </div>
        
        <div className="flex items-center gap-3">
          <Select value={optimizationStrategy} onValueChange={setOptimizationStrategy}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="aggressive">적극적</SelectItem>
              <SelectItem value="balanced">균형</SelectItem>
              <SelectItem value="conservative">보수적</SelectItem>
              <SelectItem value="cost_focused">비용 중심</SelectItem>
            </SelectContent>
          </Select>
          
          <Button
            onClick={handleAutoTuningToggle}
            disabled={isLoading}
            variant={autoTuningStatus === 'running' ? 'destructive' : 'default'}
          >
            {autoTuningStatus === 'running' ? (
              <>
                <Pause className="w-4 h-4 mr-2" />
                자동 튜닝 중지
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                자동 튜닝 시작
              </>
            )}
          </Button>
        </div>
      </div>

      {/* 메트릭 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">총 워크플로우</p>
                <p className="text-2xl font-bold text-gray-900">{metrics.totalWorkflows}</p>
              </div>
              <div className="p-3 bg-blue-100 rounded-full">
                <BarChart3 className="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <div className="mt-4">
              <div className="flex items-center text-sm">
                <span className="text-green-600 font-medium">
                  {metrics.optimizedWorkflows}개 최적화됨
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">평균 성능 향상</p>
                <p className="text-2xl font-bold text-gray-900">
                  {metrics.avgPerformanceImprovement.toFixed(1)}%
                </p>
              </div>
              <div className="p-3 bg-green-100 rounded-full">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
            </div>
            <div className="mt-4">
              <Progress value={metrics.avgPerformanceImprovement} className="h-2" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">평균 비용 절감</p>
                <p className="text-2xl font-bold text-gray-900">
                  {metrics.avgCostReduction.toFixed(1)}%
                </p>
              </div>
              <div className="p-3 bg-yellow-100 rounded-full">
                <DollarSign className="w-6 h-6 text-yellow-600" />
              </div>
            </div>
            <div className="mt-4">
              <Progress value={metrics.avgCostReduction} className="h-2" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">월간 절약</p>
                <p className="text-2xl font-bold text-gray-900">
                  ${metrics.totalMonthlySavings.toLocaleString()}
                </p>
              </div>
              <div className="p-3 bg-purple-100 rounded-full">
                <Target className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <div className="mt-4">
              <div className="flex items-center text-sm">
                <span className="text-purple-600 font-medium">
                  연간 ${(metrics.totalMonthlySavings * 12).toLocaleString()} 절약
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 탭 컨텐츠 */}
      <Tabs defaultValue="recommendations" className="space-y-6">
        <TabsList>
          <TabsTrigger value="recommendations">최적화 추천</TabsTrigger>
          <TabsTrigger value="cost-analysis">비용 분석</TabsTrigger>
          <TabsTrigger value="performance">성능 모니터링</TabsTrigger>
        </TabsList>

        {/* 최적화 추천 탭 */}
        <TabsContent value="recommendations" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5" />
                최적화 추천
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recommendations.map((rec, index) => (
                  <motion.div
                    key={rec.workflowId}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="border rounded-lg p-4 hover:bg-gray-50"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-medium text-gray-900">{rec.workflowName}</h3>
                          <Badge className={getPriorityColor(rec.priority)}>
                            {rec.priority}
                          </Badge>
                          {rec.autoApplicable && (
                            <Badge variant="outline" className="bg-blue-50 text-blue-700">
                              자동 적용 가능
                            </Badge>
                          )}
                        </div>
                        
                        <div className="text-sm text-gray-600 mb-3">
                          {rec.currentPattern} → {rec.recommendedPattern}
                        </div>
                        
                        <div className="grid grid-cols-3 gap-4 mb-3">
                          <div className="text-center">
                            <div className="text-lg font-semibold text-green-600">
                              +{rec.estimatedImprovement.performance}%
                            </div>
                            <div className="text-xs text-gray-500">성능</div>
                          </div>
                          <div className="text-center">
                            <div className="text-lg font-semibold text-blue-600">
                              -{rec.estimatedImprovement.cost}%
                            </div>
                            <div className="text-xs text-gray-500">비용</div>
                          </div>
                          <div className="text-center">
                            <div className={`text-lg font-semibold ${
                              rec.estimatedImprovement.reliability >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {rec.estimatedImprovement.reliability >= 0 ? '+' : ''}{rec.estimatedImprovement.reliability}%
                            </div>
                            <div className="text-xs text-gray-500">안정성</div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-2 text-sm">
                          <span className="text-gray-500">신뢰도:</span>
                          <span className={`font-medium ${getConfidenceColor(rec.confidence)}`}>
                            {(rec.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2 ml-4">
                        <Button
                          size="sm"
                          onClick={() => handleApplyRecommendation(rec)}
                          disabled={isLoading}
                        >
                          적용
                        </Button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 비용 분석 탭 */}
        <TabsContent value="cost-analysis" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="w-5 h-5" />
                  비용 구성
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(costBreakdown).map(([key, value]) => {
                    const labels = {
                      compute: '컴퓨팅',
                      llmApi: 'LLM API',
                      storage: '저장소',
                      network: '네트워크',
                      overhead: '오버헤드'
                    };
                    
                    const colors = {
                      compute: 'bg-blue-500',
                      llmApi: 'bg-green-500',
                      storage: 'bg-yellow-500',
                      network: 'bg-purple-500',
                      overhead: 'bg-red-500'
                    };
                    
                    return (
                      <div key={key} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-3 h-3 rounded-full ${colors[key as keyof typeof colors]}`} />
                          <span className="text-sm font-medium">{labels[key as keyof typeof labels]}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-20 bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${colors[key as keyof typeof colors]}`}
                              style={{ width: `${value}%` }}
                            />
                          </div>
                          <span className="text-sm text-gray-600 w-10 text-right">{value}%</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="w-5 h-5" />
                  비용 최적화 기회
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <AlertTriangle className="w-4 h-4 text-yellow-600" />
                      <span className="font-medium text-yellow-800">LLM 모델 최적화</span>
                    </div>
                    <p className="text-sm text-yellow-700">
                      더 효율적인 모델로 변경하여 월 $420 절약 가능
                    </p>
                  </div>
                  
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <Cpu className="w-4 h-4 text-blue-600" />
                      <span className="font-medium text-blue-800">컴퓨팅 리소스 최적화</span>
                    </div>
                    <p className="text-sm text-blue-700">
                      리소스 할당 조정으로 월 $280 절약 가능
                    </p>
                  </div>
                  
                  <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <Database className="w-4 h-4 text-green-600" />
                      <span className="font-medium text-green-800">캐싱 최적화</span>
                    </div>
                    <p className="text-sm text-green-700">
                      지능형 캐싱으로 월 $150 절약 가능
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 성능 모니터링 탭 */}
        <TabsContent value="performance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                실시간 성능 모니터링
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600 mb-2">2.3s</div>
                  <div className="text-sm text-gray-600">평균 실행 시간</div>
                  <div className="mt-2">
                    <Badge variant="outline" className="bg-green-50 text-green-700">
                      목표 달성
                    </Badge>
                  </div>
                </div>
                
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600 mb-2">94.2%</div>
                  <div className="text-sm text-gray-600">성공률</div>
                  <div className="mt-2">
                    <Badge variant="outline" className="bg-blue-50 text-blue-700">
                      우수
                    </Badge>
                  </div>
                </div>
                
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600 mb-2">$0.08</div>
                  <div className="text-sm text-gray-600">평균 실행 비용</div>
                  <div className="mt-2">
                    <Badge variant="outline" className="bg-purple-50 text-purple-700">
                      최적화됨
                    </Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};