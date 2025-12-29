"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  TrendingUp, 
  Zap, 
  Target, 
  BarChart3, 
  Settings,
  Play,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  Clock,
  DollarSign,
  Star,
  Activity,
  Lightbulb,
  GitCompare,
  History,
  Gauge
} from 'lucide-react';

interface WorkflowOptimizationBlockProps {
  id: string;
  data: any;
  onUpdate: (id: string, data: any) => void;
}

interface PerformancePrediction {
  execution_time: number;
  cost_estimate: number;
  quality_score: number;
  resource_usage: Record<string, number>;
  confidence_interval: { lower: number; upper: number };
  prediction_accuracy: number;
  bottlenecks: string[];
  optimization_suggestions: string[];
}

interface OptimizationResult {
  original_config: any;
  optimized_config: any;
  predicted_improvement: Record<string, number>;
  optimization_strategy: string;
  confidence_score: number;
  estimated_savings: Record<string, number>;
  risk_assessment: Record<string, number>;
}

const WorkflowOptimizationBlock: React.FC<WorkflowOptimizationBlockProps> = ({
  id,
  data,
  onUpdate
}) => {
  const [activeTab, setActiveTab] = useState('prediction');
  const [isProcessing, setIsProcessing] = useState(false);
  const [prediction, setPrediction] = useState<PerformancePrediction | null>(null);
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResult | null>(null);
  const [bottleneckAnalysis, setBottleneckAnalysis] = useState<any>(null);
  const [performanceHistory, setPerformanceHistory] = useState<any[]>([]);

  // 예측 설정
  const [predictionConfig, setPredictionConfig] = useState({
    tasks: data.tasks || [],
    agent_assignments: data.agent_assignments || {},
    collaboration_pattern: data.collaboration_pattern || 'pipeline'
  });

  // 최적화 설정
  const [optimizationConfig, setOptimizationConfig] = useState({
    objective: data.objective || 'balance_all',
    strategy: data.strategy || 'greedy',
    constraints: data.constraints || {}
  });

  useEffect(() => {
    loadPerformanceHistory();
  }, []);

  const loadPerformanceHistory = async () => {
    try {
      const response = await fetch('/api/agent-builder/workflow-optimization/performance-history?limit=50');
      if (response.ok) {
        const result = await response.json();
        setPerformanceHistory(result.history || []);
      }
    } catch (error) {
      console.error('Failed to load performance history:', error);
    }
  };

  const handlePerformancePrediction = async () => {
    setIsProcessing(true);
    try {
      const response = await fetch('/api/agent-builder/workflow-optimization/predict-performance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tasks: predictionConfig.tasks.length > 0 ? predictionConfig.tasks : [
            {
              task_id: 'sample_task',
              task_type: 'multimodal_analysis',
              priority: 'medium',
              requirements: { accuracy: 0.9 },
              input_data: { sample: true },
              estimated_duration: 30.0,
              dependencies: []
            }
          ],
          agent_assignments: predictionConfig.agent_assignments,
          collaboration_pattern: predictionConfig.collaboration_pattern
        })
      });

      const result = await response.json();
      if (result.success) {
        setPrediction(result.prediction);
      }
    } catch (error) {
      console.error('Performance prediction failed:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleWorkflowOptimization = async () => {
    setIsProcessing(true);
    try {
      const response = await fetch('/api/agent-builder/workflow-optimization/optimize-configuration', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tasks: predictionConfig.tasks.length > 0 ? predictionConfig.tasks : [
            {
              task_id: 'sample_task',
              task_type: 'multimodal_analysis',
              priority: 'medium',
              requirements: { accuracy: 0.9 },
              input_data: { sample: true },
              estimated_duration: 30.0,
              dependencies: []
            }
          ],
          objective: optimizationConfig.objective,
          strategy: optimizationConfig.strategy,
          constraints: optimizationConfig.constraints
        })
      });

      const result = await response.json();
      if (result.success) {
        setOptimizationResult(result.optimization);
      }
    } catch (error) {
      console.error('Workflow optimization failed:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleBottleneckAnalysis = async () => {
    setIsProcessing(true);
    try {
      const response = await fetch('/api/agent-builder/workflow-optimization/analyze-bottlenecks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tasks: predictionConfig.tasks.length > 0 ? predictionConfig.tasks : [
            {
              task_id: 'sample_task',
              task_type: 'multimodal_analysis',
              priority: 'medium',
              requirements: { accuracy: 0.9 },
              input_data: { sample: true },
              estimated_duration: 30.0,
              dependencies: []
            }
          ],
          agent_assignments: predictionConfig.agent_assignments,
          collaboration_pattern: predictionConfig.collaboration_pattern
        })
      });

      const result = await response.json();
      if (result.success) {
        setBottleneckAnalysis(result.bottleneck_analysis);
      }
    } catch (error) {
      console.error('Bottleneck analysis failed:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const updateData = (newData: any) => {
    const updatedData = { ...data, ...newData };
    onUpdate(id, updatedData);
  };

  const getConfidenceColor = (accuracy: number) => {
    if (accuracy > 0.8) return 'text-green-600';
    if (accuracy > 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getImprovementColor = (improvement: number) => {
    if (improvement > 10) return 'text-green-600';
    if (improvement > 0) return 'text-blue-600';
    return 'text-red-600';
  };

  const renderPerformancePrediction = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="collaboration-pattern">협업 패턴</Label>
          <Select
            value={predictionConfig.collaboration_pattern}
            onValueChange={(value) => setPredictionConfig(prev => ({ ...prev, collaboration_pattern: value }))}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="pipeline">파이프라인</SelectItem>
              <SelectItem value="ensemble">앙상블</SelectItem>
              <SelectItem value="hierarchical">계층적</SelectItem>
              <SelectItem value="consensus">합의</SelectItem>
              <SelectItem value="peer_to_peer">P2P</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="task-count">작업 수</Label>
          <Input
            id="task-count"
            type="number"
            value={predictionConfig.tasks.length}
            onChange={(e) => {
              const count = parseInt(e.target.value) || 1;
              const newTasks = Array.from({ length: count }, (_, i) => ({
                task_id: `task_${i + 1}`,
                task_type: 'multimodal_analysis',
                priority: 'medium',
                requirements: { accuracy: 0.9 },
                input_data: { sample: true },
                estimated_duration: 30.0,
                dependencies: []
              }));
              setPredictionConfig(prev => ({ ...prev, tasks: newTasks }));
            }}
            min="1"
            max="20"
          />
        </div>
      </div>

      <Button 
        onClick={handlePerformancePrediction} 
        disabled={isProcessing}
        className="w-full"
      >
        {isProcessing ? (
          <>
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            예측 중...
          </>
        ) : (
          <>
            <TrendingUp className="w-4 h-4 mr-2" />
            성능 예측 실행
          </>
        )}
      </Button>

      {prediction && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Gauge className="w-5 h-5 mr-2" />
              예측 결과
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <Clock className="w-8 h-8 mx-auto mb-2 text-blue-600" />
                <div className="text-2xl font-bold text-blue-600">{prediction.execution_time.toFixed(1)}s</div>
                <div className="text-sm text-blue-700">예상 실행 시간</div>
              </div>
              
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <DollarSign className="w-8 h-8 mx-auto mb-2 text-green-600" />
                <div className="text-2xl font-bold text-green-600">${prediction.cost_estimate.toFixed(3)}</div>
                <div className="text-sm text-green-700">예상 비용</div>
              </div>
              
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <Star className="w-8 h-8 mx-auto mb-2 text-purple-600" />
                <div className="text-2xl font-bold text-purple-600">{(prediction.quality_score * 100).toFixed(1)}%</div>
                <div className="text-sm text-purple-700">예상 품질</div>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>예측 신뢰도</span>
                  <span className={getConfidenceColor(prediction.prediction_accuracy)}>
                    {(prediction.prediction_accuracy * 100).toFixed(1)}%
                  </span>
                </div>
                <Progress value={prediction.prediction_accuracy * 100} className="h-2" />
              </div>

              {prediction.bottlenecks.length > 0 && (
                <div>
                  <h4 className="font-medium mb-2 flex items-center">
                    <AlertTriangle className="w-4 h-4 mr-2 text-orange-600" />
                    식별된 병목 지점
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {prediction.bottlenecks.map((bottleneck, index) => (
                      <Badge key={index} variant="destructive">{bottleneck}</Badge>
                    ))}
                  </div>
                </div>
              )}

              {prediction.optimization_suggestions.length > 0 && (
                <div>
                  <h4 className="font-medium mb-2 flex items-center">
                    <Lightbulb className="w-4 h-4 mr-2 text-yellow-600" />
                    최적화 제안
                  </h4>
                  <ul className="space-y-1">
                    {prediction.optimization_suggestions.map((suggestion, index) => (
                      <li key={index} className="text-sm text-gray-600 flex items-start">
                        <span className="w-2 h-2 bg-blue-600 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                        {suggestion}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderWorkflowOptimization = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="objective">최적화 목표</Label>
          <Select
            value={optimizationConfig.objective}
            onValueChange={(value) => setOptimizationConfig(prev => ({ ...prev, objective: value }))}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="minimize_time">실행 시간 최소화</SelectItem>
              <SelectItem value="minimize_cost">비용 최소화</SelectItem>
              <SelectItem value="maximize_quality">품질 최대화</SelectItem>
              <SelectItem value="balance_all">균형 최적화</SelectItem>
              <SelectItem value="minimize_resource">리소스 최소화</SelectItem>
              <SelectItem value="maximize_throughput">처리량 최대화</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="strategy">최적화 전략</Label>
          <Select
            value={optimizationConfig.strategy}
            onValueChange={(value) => setOptimizationConfig(prev => ({ ...prev, strategy: value }))}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="greedy">탐욕적 최적화</SelectItem>
              <SelectItem value="genetic">유전 알고리즘</SelectItem>
              <SelectItem value="annealing">시뮬레이티드 어닐링</SelectItem>
              <SelectItem value="particle_swarm">입자 군집 최적화</SelectItem>
              <SelectItem value="bayesian">베이지안 최적화</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div>
        <Label htmlFor="constraints">제약 조건 (JSON)</Label>
        <Textarea
          id="constraints"
          placeholder='{"max_cost": 1.0, "max_execution_time": 300, "required_quality": 0.85}'
          value={JSON.stringify(optimizationConfig.constraints, null, 2)}
          onChange={(e) => {
            try {
              const constraints = JSON.parse(e.target.value);
              setOptimizationConfig(prev => ({ ...prev, constraints }));
            } catch (error) {
              // 유효하지 않은 JSON은 무시
            }
          }}
          className="h-24"
        />
      </div>

      <Button 
        onClick={handleWorkflowOptimization} 
        disabled={isProcessing}
        className="w-full"
      >
        {isProcessing ? (
          <>
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            최적화 중...
          </>
        ) : (
          <>
            <Zap className="w-4 h-4 mr-2" />
            워크플로우 최적화 실행
          </>
        )}
      </Button>

      {optimizationResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Target className="w-5 h-5 mr-2" />
              최적화 결과
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <Clock className="w-8 h-8 mx-auto mb-2 text-green-600" />
                <div className={`text-2xl font-bold ${getImprovementColor(optimizationResult.predicted_improvement.execution_time || 0)}`}>
                  {(optimizationResult.predicted_improvement.execution_time || 0) > 0 ? '+' : ''}{(optimizationResult.predicted_improvement.execution_time || 0).toFixed(1)}%
                </div>
                <div className="text-sm text-green-700">시간 개선</div>
              </div>
              
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <DollarSign className="w-8 h-8 mx-auto mb-2 text-blue-600" />
                <div className={`text-2xl font-bold ${getImprovementColor(optimizationResult.predicted_improvement.cost || 0)}`}>
                  {(optimizationResult.predicted_improvement.cost || 0) > 0 ? '+' : ''}{(optimizationResult.predicted_improvement.cost || 0).toFixed(1)}%
                </div>
                <div className="text-sm text-blue-700">비용 개선</div>
              </div>
              
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <Star className="w-8 h-8 mx-auto mb-2 text-purple-600" />
                <div className={`text-2xl font-bold ${getImprovementColor(optimizationResult.predicted_improvement.quality || 0)}`}>
                  {(optimizationResult.predicted_improvement.quality || 0) > 0 ? '+' : ''}{(optimizationResult.predicted_improvement.quality || 0).toFixed(1)}%
                </div>
                <div className="text-sm text-purple-700">품질 개선</div>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>최적화 신뢰도</span>
                  <span className={getConfidenceColor(optimizationResult.confidence_score)}>
                    {(optimizationResult.confidence_score * 100).toFixed(1)}%
                  </span>
                </div>
                <Progress value={optimizationResult.confidence_score * 100} className="h-2" />
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">전략:</span> {optimizationResult.optimization_strategy}
                </div>
                <div>
                  <span className="font-medium">시간 절약:</span> {optimizationResult.estimated_savings.time_seconds?.toFixed(1)}초
                </div>
                <div>
                  <span className="font-medium">비용 절약:</span> ${optimizationResult.estimated_savings.cost_dollars?.toFixed(3)}
                </div>
                <div>
                  <span className="font-medium">품질 향상:</span> {((optimizationResult.estimated_savings.quality_improvement || 0) * 100).toFixed(1)}%
                </div>
              </div>

              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  {optimizationResult.confidence_score > 0.7 
                    ? "최적화 적용을 권장합니다." 
                    : "최적화 결과를 검토한 후 적용하세요."}
                </AlertDescription>
              </Alert>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderBottleneckAnalysis = () => (
    <div className="space-y-6">
      <Button 
        onClick={handleBottleneckAnalysis} 
        disabled={isProcessing}
        className="w-full"
      >
        {isProcessing ? (
          <>
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            분석 중...
          </>
        ) : (
          <>
            <Activity className="w-4 h-4 mr-2" />
            병목 지점 분석
          </>
        )}
      </Button>

      {bottleneckAnalysis && (
        <div className="space-y-4">
          {bottleneckAnalysis.identified_bottlenecks.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <AlertTriangle className="w-5 h-5 mr-2 text-orange-600" />
                  식별된 병목 지점
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {bottleneckAnalysis.identified_bottlenecks.map((bottleneck: string, index: number) => (
                    <div key={index} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium">{bottleneck}</h4>
                        <Badge variant="destructive">
                          {bottleneckAnalysis.bottleneck_details[bottleneck]?.severity || 'medium'}
                        </Badge>
                      </div>
                      
                      {bottleneckAnalysis.bottleneck_details[bottleneck] && (
                        <p className="text-sm text-gray-600 mb-3">
                          {bottleneckAnalysis.bottleneck_details[bottleneck].description}
                        </p>
                      )}

                      {bottleneckAnalysis.resolution_strategies[bottleneck] && (
                        <div>
                          <h5 className="font-medium text-sm mb-2">해결 전략:</h5>
                          <ul className="space-y-1">
                            {bottleneckAnalysis.resolution_strategies[bottleneck].map((strategy: string, strategyIndex: number) => (
                              <li key={strategyIndex} className="text-sm text-gray-600 flex items-start">
                                <span className="w-2 h-2 bg-blue-600 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                                {strategy}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ) : (
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                현재 설정에서 심각한 병목 지점이 발견되지 않았습니다.
              </AlertDescription>
            </Alert>
          )}

          {bottleneckAnalysis.priority_actions && bottleneckAnalysis.priority_actions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Lightbulb className="w-5 h-5 mr-2 text-yellow-600" />
                  우선순위 개선 사항
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {bottleneckAnalysis.priority_actions.map((action: any, index: number) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <div className="font-medium">{action.action}</div>
                        <div className="text-sm text-gray-600">예상 효과: {action.estimated_impact}</div>
                      </div>
                      <Badge variant={action.priority === 'high' ? 'default' : 'secondary'}>
                        {action.priority}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );

  const renderPerformanceHistory = () => (
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
              {performanceHistory.slice(0, 10).map((record, index) => (
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
            아직 실행 기록이 없습니다. 워크플로우를 실행하면 성능 데이터가 수집됩니다.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center">
          <BarChart3 className="w-6 h-6 mr-2 text-blue-600" />
          지능형 워크플로우 최적화
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="prediction">성능 예측</TabsTrigger>
            <TabsTrigger value="optimization">최적화</TabsTrigger>
            <TabsTrigger value="bottlenecks">병목 분석</TabsTrigger>
            <TabsTrigger value="history">실행 기록</TabsTrigger>
          </TabsList>

          <TabsContent value="prediction" className="mt-6">
            {renderPerformancePrediction()}
          </TabsContent>

          <TabsContent value="optimization" className="mt-6">
            {renderWorkflowOptimization()}
          </TabsContent>

          <TabsContent value="bottlenecks" className="mt-6">
            {renderBottleneckAnalysis()}
          </TabsContent>

          <TabsContent value="history" className="mt-6">
            {renderPerformanceHistory()}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default WorkflowOptimizationBlock;