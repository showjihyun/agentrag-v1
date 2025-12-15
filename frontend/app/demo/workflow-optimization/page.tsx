"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  BarChart3, 
  TrendingUp, 
  Zap, 
  Target, 
  Clock,
  DollarSign,
  Star,
  Activity,
  Lightbulb,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  Play,
  Settings,
  Gauge,
  History
} from 'lucide-react';

interface OptimizationScenario {
  id: string;
  name: string;
  description: string;
  objective: string;
  strategy: string;
  tasks: any[];
  expectedImprovement: {
    time: number;
    cost: number;
    quality: number;
  };
}

const optimizationScenarios: OptimizationScenario[] = [
  {
    id: 'time_critical',
    name: '시간 중심 최적화',
    description: '실시간 처리가 필요한 워크플로우의 실행 시간을 최소화',
    objective: 'minimize_time',
    strategy: 'greedy',
    tasks: [
      {
        task_id: 'realtime_analysis',
        task_type: 'image_analysis',
        priority: 'critical',
        requirements: { real_time: true, accuracy: 0.85 },
        estimated_duration: 45.0
      },
      {
        task_id: 'quick_response',
        task_type: 'text_processing',
        priority: 'high',
        requirements: { response_time: 'fast' },
        estimated_duration: 20.0
      }
    ],
    expectedImprovement: { time: 35, cost: -10, quality: -5 }
  },
  {
    id: 'cost_efficient',
    name: '비용 효율 최적화',
    description: '대량 배치 처리 작업의 비용을 최소화하면서 품질 유지',
    objective: 'minimize_cost',
    strategy: 'genetic',
    tasks: [
      {
        task_id: 'batch_processing',
        task_type: 'document_processing',
        priority: 'medium',
        requirements: { batch_size: 1000, cost_limit: 0.5 },
        estimated_duration: 120.0
      },
      {
        task_id: 'bulk_analysis',
        task_type: 'data_analysis',
        priority: 'medium',
        requirements: { volume: 'high' },
        estimated_duration: 90.0
      }
    ],
    expectedImprovement: { time: -15, cost: 40, quality: 5 }
  },
  {
    id: 'quality_focused',
    name: '품질 중심 최적화',
    description: '중요한 의사결정을 위한 고품질 분석 결과 생성',
    objective: 'maximize_quality',
    strategy: 'annealing',
    tasks: [
      {
        task_id: 'precision_analysis',
        task_type: 'multimodal_fusion',
        priority: 'critical',
        requirements: { accuracy: 0.95, precision: 0.9 },
        estimated_duration: 180.0
      },
      {
        task_id: 'validation_check',
        task_type: 'quality_assurance',
        priority: 'high',
        requirements: { validation_level: 'strict' },
        estimated_duration: 60.0
      }
    ],
    expectedImprovement: { time: -20, cost: -25, quality: 30 }
  },
  {
    id: 'balanced_approach',
    name: '균형 최적화',
    description: '시간, 비용, 품질의 최적 균형점을 찾는 범용 최적화',
    objective: 'balance_all',
    strategy: 'particle_swarm',
    tasks: [
      {
        task_id: 'general_processing',
        task_type: 'mixed_workload',
        priority: 'medium',
        requirements: { balance: true },
        estimated_duration: 75.0
      },
      {
        task_id: 'adaptive_analysis',
        task_type: 'adaptive_processing',
        priority: 'medium',
        requirements: { flexibility: 'high' },
        estimated_duration: 55.0
      }
    ],
    expectedImprovement: { time: 15, cost: 20, quality: 12 }
  }
];

const WorkflowOptimizationDemo: React.FC = () => {
  const [activeTab, setActiveTab] = useState('scenarios');
  const [selectedScenario, setSelectedScenario] = useState<OptimizationScenario | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [predictionResult, setPredictionResult] = useState<any>(null);
  const [optimizationResult, setOptimizationResult] = useState<any>(null);
  const [bottleneckAnalysis, setBottleneckAnalysis] = useState<any>(null);
  const [performanceHistory, setPerformanceHistory] = useState<any[]>([]);
  const [comparisonResults, setComparisonResults] = useState<any>(null);

  useEffect(() => {
    loadPerformanceHistory();
  }, []);

  const loadPerformanceHistory = async () => {
    try {
      const response = await fetch('/api/agent-builder/workflow-optimization/performance-history?limit=20');
      if (response.ok) {
        const result = await response.json();
        setPerformanceHistory(result.history || []);
      }
    } catch (error) {
      console.error('Failed to load performance history:', error);
    }
  };

  const runOptimizationDemo = async (scenario: OptimizationScenario) => {
    setSelectedScenario(scenario);
    setIsProcessing(true);
    setPredictionResult(null);
    setOptimizationResult(null);
    setBottleneckAnalysis(null);

    try {
      // 1단계: 성능 예측
      console.log('🔍 성능 예측 실행 중...');
      const predictionResponse = await fetch('/api/agent-builder/workflow-optimization/predict-performance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tasks: scenario.tasks,
          collaboration_pattern: 'pipeline'
        })
      });

      const predictionData = await predictionResponse.json();
      setPredictionResult(predictionData);

      // 2단계: 워크플로우 최적화
      console.log('⚡ 워크플로우 최적화 실행 중...');
      const optimizationResponse = await fetch('/api/agent-builder/workflow-optimization/optimize-configuration', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tasks: scenario.tasks,
          objective: scenario.objective,
          strategy: scenario.strategy,
          constraints: {
            max_execution_time: 300,
            required_quality: 0.8
          }
        })
      });

      const optimizationData = await optimizationResponse.json();
      setOptimizationResult(optimizationData);

      // 3단계: 병목 분석
      console.log('🔍 병목 지점 분석 중...');
      const bottleneckResponse = await fetch('/api/agent-builder/workflow-optimization/analyze-bottlenecks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tasks: scenario.tasks,
          collaboration_pattern: 'pipeline'
        })
      });

      const bottleneckData = await bottleneckResponse.json();
      setBottleneckAnalysis(bottleneckData);

      // 성능 히스토리 새로고침
      await loadPerformanceHistory();

    } catch (error) {
      console.error('Optimization demo failed:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const runComparisonDemo = async () => {
    setIsProcessing(true);
    try {
      const sampleTasks = [
        {
          task_id: 'comparison_task',
          task_type: 'multimodal_analysis',
          priority: 'medium',
          requirements: { accuracy: 0.9 },
          estimated_duration: 60.0
        }
      ];

      const configurations = [
        {
          name: 'Pipeline Configuration',
          collaboration_pattern: 'pipeline',
          agent_assignments: { 'comparison_task': 'agent_1' }
        },
        {
          name: 'Ensemble Configuration',
          collaboration_pattern: 'ensemble',
          agent_assignments: { 'comparison_task': 'agent_2' }
        },
        {
          name: 'Hierarchical Configuration',
          collaboration_pattern: 'hierarchical',
          agent_assignments: { 'comparison_task': 'agent_3' }
        }
      ];

      const response = await fetch('/api/agent-builder/workflow-optimization/compare-configurations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tasks: sampleTasks,
          configurations: configurations
        })
      });

      const result = await response.json();
      setComparisonResults(result);

    } catch (error) {
      console.error('Comparison demo failed:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const getImprovementColor = (improvement: number) => {
    if (improvement > 10) return 'text-green-600';
    if (improvement > 0) return 'text-blue-600';
    return 'text-red-600';
  };

  const getObjectiveIcon = (objective: string) => {
    switch (objective) {
      case 'minimize_time': return <Clock className="w-5 h-5" />;
      case 'minimize_cost': return <DollarSign className="w-5 h-5" />;
      case 'maximize_quality': return <Star className="w-5 h-5" />;
      case 'balance_all': return <Target className="w-5 h-5" />;
      default: return <Settings className="w-5 h-5" />;
    }
  };

  const renderScenarios = () => (
    <div className="space-y-6">
      <Alert>
        <Lightbulb className="h-4 w-4" />
        <AlertDescription>
          다양한 최적화 시나리오를 통해 지능형 워크플로우 최적화 기능을 체험해보세요.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {optimizationScenarios.map((scenario) => (
          <Card key={scenario.id} className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center">
                  {getObjectiveIcon(scenario.objective)}
                  <span className="ml-2">{scenario.name}</span>
                </CardTitle>
                <Badge variant="outline">{scenario.strategy}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 mb-4">{scenario.description}</p>
              
              <div className="space-y-2 text-sm mb-4">
                <div className="flex justify-between">
                  <span className="font-medium">작업 수:</span>
                  <span>{scenario.tasks.length}개</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">최적화 목표:</span>
                  <span>{scenario.objective}</span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 mb-4">
                <div className="text-center p-2 bg-blue-50 rounded">
                  <div className={`font-bold ${getImprovementColor(scenario.expectedImprovement.time)}`}>
                    {scenario.expectedImprovement.time > 0 ? '+' : ''}{scenario.expectedImprovement.time}%
                  </div>
                  <div className="text-xs text-gray-600">시간</div>
                </div>
                <div className="text-center p-2 bg-green-50 rounded">
                  <div className={`font-bold ${getImprovementColor(scenario.expectedImprovement.cost)}`}>
                    {scenario.expectedImprovement.cost > 0 ? '+' : ''}{scenario.expectedImprovement.cost}%
                  </div>
                  <div className="text-xs text-gray-600">비용</div>
                </div>
                <div className="text-center p-2 bg-purple-50 rounded">
                  <div className={`font-bold ${getImprovementColor(scenario.expectedImprovement.quality)}`}>
                    {scenario.expectedImprovement.quality > 0 ? '+' : ''}{scenario.expectedImprovement.quality}%
                  </div>
                  <div className="text-xs text-gray-600">품질</div>
                </div>
              </div>

              <Button 
                onClick={() => runOptimizationDemo(scenario)}
                disabled={isProcessing}
                className="w-full"
              >
                {isProcessing && selectedScenario?.id === scenario.id ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    최적화 중...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    시나리오 실행
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderResults = () => (
    <div className="space-y-6">
      {selectedScenario && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Target className="w-5 h-5 mr-2" />
              실행 중인 시나리오: {selectedScenario.name}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">{selectedScenario.description}</p>
          </CardContent>
        </Card>
      )}

      {predictionResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Gauge className="w-5 h-5 mr-2" />
              1단계: 성능 예측 결과
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <Clock className="w-8 h-8 mx-auto mb-2 text-blue-600" />
                <div className="text-2xl font-bold text-blue-600">
                  {predictionResult.prediction.execution_time.toFixed(1)}s
                </div>
                <div className="text-sm text-blue-700">예상 실행 시간</div>
              </div>
              
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <DollarSign className="w-8 h-8 mx-auto mb-2 text-green-600" />
                <div className="text-2xl font-bold text-green-600">
                  ${predictionResult.prediction.cost_estimate.toFixed(3)}
                </div>
                <div className="text-sm text-green-700">예상 비용</div>
              </div>
              
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <Star className="w-8 h-8 mx-auto mb-2 text-purple-600" />
                <div className="text-2xl font-bold text-purple-600">
                  {(predictionResult.prediction.quality_score * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-purple-700">예상 품질</div>
              </div>
            </div>

            {predictionResult.prediction.bottlenecks.length > 0 && (
              <div className="mb-4">
                <h4 className="font-medium mb-2 flex items-center">
                  <AlertTriangle className="w-4 h-4 mr-2 text-orange-600" />
                  식별된 병목 지점
                </h4>
                <div className="flex flex-wrap gap-2">
                  {predictionResult.prediction.bottlenecks.map((bottleneck: string, index: number) => (
                    <Badge key={index} variant="destructive">{bottleneck}</Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {optimizationResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Zap className="w-5 h-5 mr-2" />
              2단계: 최적화 결과
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <Clock className="w-8 h-8 mx-auto mb-2 text-green-600" />
                <div className={`text-2xl font-bold ${getImprovementColor(optimizationResult.optimization.predicted_improvement.execution_time)}`}>
                  {optimizationResult.optimization.predicted_improvement.execution_time > 0 ? '+' : ''}
                  {optimizationResult.optimization.predicted_improvement.execution_time.toFixed(1)}%
                </div>
                <div className="text-sm text-green-700">시간 개선</div>
              </div>
              
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <DollarSign className="w-8 h-8 mx-auto mb-2 text-blue-600" />
                <div className={`text-2xl font-bold ${getImprovementColor(optimizationResult.optimization.predicted_improvement.cost)}`}>
                  {optimizationResult.optimization.predicted_improvement.cost > 0 ? '+' : ''}
                  {optimizationResult.optimization.predicted_improvement.cost.toFixed(1)}%
                </div>
                <div className="text-sm text-blue-700">비용 개선</div>
              </div>
              
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <Star className="w-8 h-8 mx-auto mb-2 text-purple-600" />
                <div className={`text-2xl font-bold ${getImprovementColor(optimizationResult.optimization.predicted_improvement.quality)}`}>
                  {optimizationResult.optimization.predicted_improvement.quality > 0 ? '+' : ''}
                  {optimizationResult.optimization.predicted_improvement.quality.toFixed(1)}%
                </div>
                <div className="text-sm text-purple-700">품질 개선</div>
              </div>
            </div>

            <div className="p-4 bg-green-50 rounded-lg">
              <h4 className="font-medium text-green-800 mb-2">최적화 요약</h4>
              <div className="text-sm text-green-700 space-y-1">
                <div>전략: {optimizationResult.optimization.optimization_strategy}</div>
                <div>신뢰도: {(optimizationResult.optimization.confidence_score * 100).toFixed(1)}%</div>
                <div>권장사항: {optimizationResult.summary.recommendation}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {bottleneckAnalysis && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              3단계: 병목 분석 결과
            </CardTitle>
          </CardHeader>
          <CardContent>
            {bottleneckAnalysis.bottleneck_analysis.identified_bottlenecks.length > 0 ? (
              <div className="space-y-4">
                {bottleneckAnalysis.bottleneck_analysis.identified_bottlenecks.map((bottleneck: string, index: number) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <h4 className="font-medium mb-2">{bottleneck}</h4>
                    {bottleneckAnalysis.bottleneck_analysis.bottleneck_details[bottleneck] && (
                      <p className="text-sm text-gray-600 mb-2">
                        {bottleneckAnalysis.bottleneck_analysis.bottleneck_details[bottleneck].description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  심각한 병목 지점이 발견되지 않았습니다.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderComparison = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">설정 비교 분석</h3>
        <Button onClick={runComparisonDemo} disabled={isProcessing}>
          {isProcessing ? (
            <>
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              비교 중...
            </>
          ) : (
            <>
              <BarChart3 className="w-4 h-4 mr-2" />
              비교 실행
            </>
          )}
        </Button>
      </div>

      {comparisonResults && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="w-5 h-5 mr-2" />
              설정 비교 결과
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {comparisonResults.comparison.configurations.map((config: any, index: number) => (
                <div key={index} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium">{config.configuration_id}</h4>
                    <Badge variant={index === 0 ? 'default' : 'secondary'}>
                      {index === 0 ? '최적' : `${index + 1}위`}
                    </Badge>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="font-medium">실행 시간:</span> {config.prediction.execution_time.toFixed(1)}s
                    </div>
                    <div>
                      <span className="font-medium">비용:</span> ${config.prediction.cost_estimate.toFixed(3)}
                    </div>
                    <div>
                      <span className="font-medium">품질:</span> {(config.prediction.quality_score * 100).toFixed(1)}%
                    </div>
                  </div>
                  
                  <div className="mt-2">
                    <div className="flex justify-between text-sm mb-1">
                      <span>종합 점수</span>
                      <span>{config.scores.overall_score.toFixed(1)}</span>
                    </div>
                    <Progress value={(config.scores.overall_score / 100) * 100} className="h-2" />
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-800 mb-2">비교 요약</h4>
              <div className="text-sm text-blue-700 space-y-1">
                <div>가장 빠른 설정: {comparisonResults.comparison.summary.fastest}</div>
                <div>가장 저렴한 설정: {comparisonResults.comparison.summary.cheapest}</div>
                <div>가장 높은 품질: {comparisonResults.comparison.summary.highest_quality}</div>
                <div>가장 균형잡힌 설정: {comparisonResults.comparison.summary.most_balanced}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderHistory = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">성능 히스토리</h3>
        <Button onClick={loadPerformanceHistory} variant="outline" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" />
          새로고침
        </Button>
      </div>

      {performanceHistory.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <History className="w-5 h-5 mr-2" />
              최근 실행 기록 ({performanceHistory.length}개)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {performanceHistory.map((record, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <div className="font-medium">{record.workflow_id}</div>
                    <div className="text-sm text-gray-600">
                      {new Date(record.timestamp).toLocaleString()}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm">
                      <span className="font-medium">{record.execution_time.toFixed(1)}s</span>
                      <span className="text-gray-600 ml-2">${record.cost.toFixed(3)}</span>
                    </div>
                    <div className="text-sm text-gray-600">
                      품질: {(record.quality_score * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : (
        <Alert>
          <History className="h-4 w-4" />
          <AlertDescription>
            아직 실행 기록이 없습니다. 최적화 시나리오를 실행하면 성능 데이터가 수집됩니다.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-4 flex items-center">
          <BarChart3 className="w-8 h-8 mr-3 text-blue-600" />
          지능형 워크플로우 최적화 데모
        </h1>
        <p className="text-gray-600 text-lg">
          예측 성능 모델링, 고급 리소스 최적화, 병목 분석 등의 지능형 최적화 기능을 체험해보세요.
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="scenarios">최적화 시나리오</TabsTrigger>
          <TabsTrigger value="results">실행 결과</TabsTrigger>
          <TabsTrigger value="comparison">설정 비교</TabsTrigger>
          <TabsTrigger value="history">성능 히스토리</TabsTrigger>
        </TabsList>

        <TabsContent value="scenarios" className="mt-6">
          {renderScenarios()}
        </TabsContent>

        <TabsContent value="results" className="mt-6">
          {renderResults()}
        </TabsContent>

        <TabsContent value="comparison" className="mt-6">
          {renderComparison()}
        </TabsContent>

        <TabsContent value="history" className="mt-6">
          {renderHistory()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default WorkflowOptimizationDemo;