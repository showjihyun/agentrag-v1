'use client';

/**
 * Predictive Routing Block
 * AI 기반 예측적 라우팅 및 지능형 전략 선택 블록
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import {
  Brain,
  Zap,
  Target,
  TrendingUp,
  Clock,
  DollarSign,
  Cpu,
  Activity,
  BarChart3,
  Settings,
  Lightbulb,
  CheckCircle,
  AlertCircle,
  Info,
  Loader2,
  RefreshCw,
  Route,
  Gauge,
  Network,
  Sparkles,
  ArrowRight,
  Users,
  Calendar,
  MapPin
} from 'lucide-react';

interface PredictiveRoutingBlockProps {
  blockId: string;
  config?: any;
  onConfigChange?: (config: any) => void;
  onExecute?: (result: any) => void;
  isExecuting?: boolean;
}

interface RoutingRequest {
  content_profile: any;
  user_preferences: Record<string, any>;
  business_priority: string;
  deadline_constraint?: string;
  budget_limit?: number;
  quality_threshold: number;
  request_data: Record<string, any>;
}

interface RoutingDecision {
  routing_id: string;
  selected_strategy: string;
  processing_mode: string;
  model_selection: string;
  configuration: Record<string, any>;
  confidence_score: number;
  reasoning: string;
  estimated_performance: Record<string, any>;
  fallback_options: Array<any>;
  monitoring_metrics: string[];
  execution_plan: {
    steps: string[];
    estimated_total_time: number;
    resource_requirements: Record<string, string>;
  };
}

export default function PredictiveRoutingBlock({
  blockId,
  config = {},
  onConfigChange,
  onExecute,
  isExecuting = false
}: PredictiveRoutingBlockProps) {
  const { toast } = useToast();
  
  // State
  const [routingRequest, setRoutingRequest] = useState<RoutingRequest>({
    content_profile: {
      file_size_mb: 25,
      duration_seconds: 300,
      has_audio: true,
      user_priority: 'balanced',
      min_accuracy_threshold: 0.85,
      batch_size: 1,
      is_realtime: false,
      user_experience_level: 'intermediate'
    },
    user_preferences: {},
    business_priority: 'medium',
    quality_threshold: 0.85,
    request_data: {}
  });
  
  const [routingDecision, setRoutingDecision] = useState<RoutingDecision | null>(null);
  const [isRouting, setIsRouting] = useState(false);
  const [strategies, setStrategies] = useState<any[]>([]);
  const [processingModes, setProcessingModes] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [systemMetrics, setSystemMetrics] = useState<any>(null);
  const [predictions, setPredictions] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('routing');
  
  // Load initial data
  useEffect(() => {
    loadStrategies();
    loadProcessingModes();
    loadAnalytics();
    loadSystemMetrics();
    loadPredictions();
  }, []);
  
  // Update config when routing request changes
  useEffect(() => {
    if (onConfigChange) {
      onConfigChange({
        ...config,
        routingRequest,
        routingDecision
      });
    }
  }, [routingRequest, routingDecision, onConfigChange]);
  
  const loadStrategies = async () => {
    try {
      const response = await fetch('/api/agent-builder/predictive-routing/strategies');
      const data = await response.json();
      if (data.success) {
        setStrategies(data.strategies);
      }
    } catch (error) {
      console.error('Failed to load strategies:', error);
    }
  };
  
  const loadProcessingModes = async () => {
    try {
      const response = await fetch('/api/agent-builder/predictive-routing/processing-modes');
      const data = await response.json();
      if (data.success) {
        setProcessingModes(data.processing_modes);
      }
    } catch (error) {
      console.error('Failed to load processing modes:', error);
    }
  };
  
  const loadAnalytics = async () => {
    try {
      const response = await fetch('/api/agent-builder/predictive-routing/analytics');
      const data = await response.json();
      if (data.success) {
        setAnalytics(data.analytics);
      }
    } catch (error) {
      console.error('Failed to load analytics:', error);
    }
  };
  
  const loadSystemMetrics = async () => {
    try {
      const response = await fetch('/api/agent-builder/predictive-routing/health');
      const data = await response.json();
      if (data.success) {
        setSystemMetrics(data.details);
      }
    } catch (error) {
      console.error('Failed to load system metrics:', error);
    }
  };
  
  const loadPredictions = async () => {
    try {
      const response = await fetch('/api/agent-builder/predictive-routing/predictions/performance?hours_ahead=24');
      const data = await response.json();
      if (data.success) {
        setPredictions(data);
      }
    } catch (error) {
      console.error('Failed to load predictions:', error);
    }
  };
  
  const handleRoute = async () => {
    setIsRouting(true);
    setActiveTab('results');
    
    try {
      const response = await fetch('/api/agent-builder/predictive-routing/route', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(routingRequest)
      });
      
      const data = await response.json();
      
      if (data.success && data.routing_decision) {
        setRoutingDecision(data.routing_decision);
        toast({
          title: '🧠 지능형 라우팅 완료',
          description: `${data.processing_time_seconds.toFixed(2)}초 만에 최적 경로를 찾았습니다!`,
        });
        
        // Execute with routing decision if onExecute is provided
        if (onExecute) {
          onExecute({
            type: 'predictive_routing',
            request: routingRequest,
            decision: data.routing_decision,
            processing_time: data.processing_time_seconds
          });
        }
      } else {
        throw new Error(data.error || 'Routing failed');
      }
    } catch (error) {
      console.error('Routing failed:', error);
      toast({
        title: '❌ 라우팅 실패',
        description: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.',
        variant: 'destructive'
      });
    } finally {
      setIsRouting(false);
    }
  };
  
  const getStrategyIcon = (strategyId: string) => {
    switch (strategyId) {
      case 'performance_first': return Zap;
      case 'cost_optimized': return DollarSign;
      case 'quality_assured': return Target;
      case 'adaptive_learning': return Brain;
      case 'predictive_scaling': return TrendingUp;
      default: return Settings;
    }
  };
  
  const getStrategyColor = (strategyId: string) => {
    switch (strategyId) {
      case 'performance_first': return 'text-blue-600';
      case 'cost_optimized': return 'text-green-600';
      case 'quality_assured': return 'text-purple-600';
      case 'adaptive_learning': return 'text-orange-600';
      case 'predictive_scaling': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };
  
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600';
    if (confidence >= 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };
  
  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.9) return { variant: 'default' as const, text: '높음' };
    if (confidence >= 0.7) return { variant: 'secondary' as const, text: '보통' };
    return { variant: 'destructive' as const, text: '낮음' };
  };
  
  return (
    <Card className="w-full max-w-6xl">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-purple-500">
            <Route className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold">Predictive Routing</h3>
            <p className="text-sm text-muted-foreground font-normal">
              AI 기반 예측적 라우팅 및 지능형 전략 선택
            </p>
          </div>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="routing" className="flex items-center gap-2">
              <Route className="h-4 w-4" />
              라우팅
            </TabsTrigger>
            <TabsTrigger value="results" className="flex items-center gap-2">
              <Target className="h-4 w-4" />
              결과
            </TabsTrigger>
            <TabsTrigger value="analytics" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              분석
            </TabsTrigger>
            <TabsTrigger value="predictions" className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              예측
            </TabsTrigger>
            <TabsTrigger value="system" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              시스템
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="routing" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* 콘텐츠 프로필 */}
              <div className="space-y-4">
                <h4 className="font-semibold flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  콘텐츠 프로필
                </h4>
                
                <div className="space-y-3">
                  <div>
                    <Label htmlFor="file-size">파일 크기 (MB)</Label>
                    <Input
                      id="file-size"
                      type="number"
                      value={routingRequest.content_profile.file_size_mb}
                      onChange={(e) => setRoutingRequest(prev => ({
                        ...prev,
                        content_profile: {
                          ...prev.content_profile,
                          file_size_mb: parseFloat(e.target.value) || 0
                        }
                      }))}
                      min="0"
                      step="0.1"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="duration">길이 (초)</Label>
                    <Input
                      id="duration"
                      type="number"
                      value={routingRequest.content_profile.duration_seconds}
                      onChange={(e) => setRoutingRequest(prev => ({
                        ...prev,
                        content_profile: {
                          ...prev.content_profile,
                          duration_seconds: parseFloat(e.target.value) || 0
                        }
                      }))}
                      min="0"
                      step="1"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="priority">사용자 우선순위</Label>
                    <Select
                      value={routingRequest.content_profile.user_priority}
                      onValueChange={(value) => setRoutingRequest(prev => ({
                        ...prev,
                        content_profile: {
                          ...prev.content_profile,
                          user_priority: value
                        }
                      }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="speed_first">속도 우선</SelectItem>
                        <SelectItem value="accuracy_first">정확도 우선</SelectItem>
                        <SelectItem value="balanced">균형</SelectItem>
                        <SelectItem value="cost_efficient">비용 효율</SelectItem>
                        <SelectItem value="quality_premium">품질 프리미엄</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="realtime"
                      checked={routingRequest.content_profile.is_realtime}
                      onChange={(e) => setRoutingRequest(prev => ({
                        ...prev,
                        content_profile: {
                          ...prev.content_profile,
                          is_realtime: e.target.checked
                        }
                      }))}
                      className="rounded"
                    />
                    <Label htmlFor="realtime">실시간 처리</Label>
                  </div>
                </div>
              </div>
              
              {/* 비즈니스 요구사항 */}
              <div className="space-y-4">
                <h4 className="font-semibold flex items-center gap-2">
                  <Target className="h-4 w-4" />
                  비즈니스 요구사항
                </h4>
                
                <div className="space-y-3">
                  <div>
                    <Label htmlFor="business-priority">비즈니스 우선순위</Label>
                    <Select
                      value={routingRequest.business_priority}
                      onValueChange={(value) => setRoutingRequest(prev => ({
                        ...prev,
                        business_priority: value
                      }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="critical">긴급</SelectItem>
                        <SelectItem value="high">높음</SelectItem>
                        <SelectItem value="medium">보통</SelectItem>
                        <SelectItem value="low">낮음</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="quality-threshold">품질 임계값 (%)</Label>
                    <Input
                      id="quality-threshold"
                      type="number"
                      value={Math.round(routingRequest.quality_threshold * 100)}
                      onChange={(e) => setRoutingRequest(prev => ({
                        ...prev,
                        quality_threshold: (parseFloat(e.target.value) || 85) / 100
                      }))}
                      min="50"
                      max="100"
                      step="5"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="budget-limit">예산 제한 ($)</Label>
                    <Input
                      id="budget-limit"
                      type="number"
                      value={routingRequest.budget_limit || ''}
                      onChange={(e) => {
                        const value = e.target.value ? parseFloat(e.target.value) : undefined;
                        setRoutingRequest(prev => {
                          const newRequest = { ...prev };
                          if (value !== undefined) {
                            newRequest.budget_limit = value;
                          } else {
                            delete newRequest.budget_limit;
                          }
                          return newRequest;
                        });
                      }}
                      placeholder="제한 없음"
                      min="0"
                      step="0.01"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="deadline">데드라인</Label>
                    <Input
                      id="deadline"
                      type="datetime-local"
                      value={routingRequest.deadline_constraint || ''}
                      onChange={(e) => {
                        const value = e.target.value || undefined;
                        setRoutingRequest(prev => {
                          const newRequest = { ...prev };
                          if (value !== undefined) {
                            newRequest.deadline_constraint = value;
                          } else {
                            delete newRequest.deadline_constraint;
                          }
                          return newRequest;
                        });
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>
            
            {/* 사용 가능한 전략 미리보기 */}
            <div className="space-y-4">
              <h4 className="font-semibold flex items-center gap-2">
                <Lightbulb className="h-4 w-4" />
                사용 가능한 라우팅 전략
              </h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {strategies.map((strategy) => {
                  const Icon = getStrategyIcon(strategy.id);
                  return (
                    <Card key={strategy.id} className="p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-start gap-3">
                        <div className={`p-2 rounded-lg bg-gray-100 dark:bg-gray-800`}>
                          <Icon className={`h-4 w-4 ${getStrategyColor(strategy.id)}`} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h5 className="font-medium text-sm">{strategy.name}</h5>
                          <p className="text-xs text-muted-foreground mt-1">
                            {strategy.description}
                          </p>
                          <div className="flex flex-wrap gap-1 mt-2">
                            <Badge variant="outline" className="text-xs">
                              {strategy.characteristics.speed}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {strategy.characteristics.cost}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    </Card>
                  );
                })}
              </div>
            </div>
            
            {/* 라우팅 실행 버튼 */}
            <div className="flex justify-center pt-4">
              <Button
                onClick={handleRoute}
                disabled={isRouting || isExecuting}
                size="lg"
                className="gap-2"
              >
                {isRouting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    지능형 라우팅 중...
                  </>
                ) : (
                  <>
                    <Brain className="h-4 w-4" />
                    AI 라우팅 실행
                  </>
                )}
              </Button>
            </div>
          </TabsContent>
          
          <TabsContent value="results" className="space-y-6">
            {isRouting ? (
              <div className="text-center py-12">
                <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
                <h3 className="text-lg font-semibold mb-2">AI가 최적 라우팅 경로를 분석 중입니다...</h3>
                <p className="text-muted-foreground">
                  시스템 부하, 사용자 패턴, 성능 히스토리를 종합하여 최적화하고 있습니다.
                </p>
              </div>
            ) : routingDecision ? (
              <div className="space-y-6">
                {/* 라우팅 결정 */}
                <Card className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                      <Target className="h-5 w-5" />
                      라우팅 결정
                    </h3>
                    <Badge {...getConfidenceBadge(routingDecision.confidence_score)}>
                      신뢰도: {getConfidenceBadge(routingDecision.confidence_score).text}
                    </Badge>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="font-medium">선택된 전략:</span>
                        <Badge variant="outline">{routingDecision.selected_strategy}</Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-medium">처리 모드:</span>
                        <Badge variant="outline">{routingDecision.processing_mode}</Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-medium">모델 선택:</span>
                        <Badge variant="outline">{routingDecision.model_selection}</Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-medium">라우팅 ID:</span>
                        <span className="text-sm font-mono">{routingDecision.routing_id}</span>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="font-medium">예상 처리 시간:</span>
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span>{routingDecision.estimated_performance.processing_time?.toFixed(1)}초</span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="font-medium">예상 정확도:</span>
                        <div className="flex items-center gap-2">
                          <TrendingUp className="h-4 w-4 text-muted-foreground" />
                          <span>{(routingDecision.estimated_performance.accuracy * 100)?.toFixed(1)}%</span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="font-medium">예상 비용:</span>
                        <div className="flex items-center gap-2">
                          <DollarSign className="h-4 w-4 text-muted-foreground" />
                          <span>${routingDecision.estimated_performance.cost?.toFixed(3)}</span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="font-medium">신뢰도:</span>
                        <div className="flex items-center gap-2">
                          <Progress 
                            value={routingDecision.confidence_score * 100} 
                            className="w-16 h-2"
                          />
                          <span className={getConfidenceColor(routingDecision.confidence_score)}>
                            {(routingDecision.confidence_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-4 p-4 bg-muted rounded-lg">
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <Brain className="h-4 w-4" />
                      AI 라우팅 근거
                    </h4>
                    <p className="text-sm text-muted-foreground">{routingDecision.reasoning}</p>
                  </div>
                </Card>
                
                {/* 실행 계획 */}
                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <MapPin className="h-5 w-5" />
                    실행 계획
                  </h3>
                  
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center p-4 bg-muted rounded-lg">
                        <Clock className="h-8 w-8 mx-auto mb-2 text-blue-500" />
                        <div className="font-medium">{routingDecision.execution_plan.estimated_total_time}초</div>
                        <div className="text-sm text-muted-foreground">예상 총 시간</div>
                      </div>
                      <div className="text-center p-4 bg-muted rounded-lg">
                        <Cpu className="h-8 w-8 mx-auto mb-2 text-green-500" />
                        <div className="font-medium">{routingDecision.execution_plan.resource_requirements.cpu}</div>
                        <div className="text-sm text-muted-foreground">CPU 요구사항</div>
                      </div>
                      <div className="text-center p-4 bg-muted rounded-lg">
                        <Activity className="h-8 w-8 mx-auto mb-2 text-purple-500" />
                        <div className="font-medium">{routingDecision.execution_plan.resource_requirements.memory}</div>
                        <div className="text-sm text-muted-foreground">메모리 요구사항</div>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-2">실행 단계:</h4>
                      <div className="space-y-2">
                        {routingDecision.execution_plan.steps.map((step, index) => (
                          <div key={index} className="flex items-center gap-3 p-2 border rounded">
                            <div className="w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs flex items-center justify-center">
                              {index + 1}
                            </div>
                            <span className="text-sm">{step}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </Card>
                
                {/* 폴백 옵션 */}
                {routingDecision.fallback_options.length > 0 && (
                  <Card className="p-6">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                      <RefreshCw className="h-5 w-5" />
                      폴백 옵션
                    </h3>
                    
                    <div className="grid gap-4">
                      {routingDecision.fallback_options.map((option, index) => (
                        <div key={index} className="p-4 border rounded-lg">
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="font-medium">{option.name}</h4>
                            <Badge variant="secondary">{option.strategy}</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mb-3">{option.description}</p>
                          
                          <div className="text-xs text-muted-foreground">
                            <strong>트리거 조건:</strong> {option.trigger_condition}
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}
                
                {/* 모니터링 지표 */}
                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Gauge className="h-5 w-5" />
                    모니터링 지표
                  </h3>
                  
                  <div className="flex flex-wrap gap-2">
                    {routingDecision.monitoring_metrics.map((metric, index) => (
                      <Badge key={index} variant="outline" className="gap-1">
                        <Activity className="h-3 w-3" />
                        {metric}
                      </Badge>
                    ))}
                  </div>
                </Card>
              </div>
            ) : (
              <div className="text-center py-12">
                <Route className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">라우팅 결과가 없습니다</h3>
                <p className="text-muted-foreground mb-4">
                  라우팅 탭에서 설정을 입력하고 AI 라우팅을 실행해보세요.
                </p>
                <Button onClick={() => setActiveTab('routing')} variant="outline">
                  라우팅 설정하기
                </Button>
              </div>
            )}
          </TabsContent>
          
          <TabsContent value="analytics" className="space-y-4">
            {analytics ? (
              <div className="grid gap-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <Card className="p-4">
                    <div className="text-2xl font-bold">{analytics.summary.total_requests}</div>
                    <div className="text-sm text-muted-foreground">총 요청 수</div>
                  </Card>
                  <Card className="p-4">
                    <div className="text-2xl font-bold">{(analytics.summary.avg_confidence * 100).toFixed(0)}%</div>
                    <div className="text-sm text-muted-foreground">평균 신뢰도</div>
                  </Card>
                  <Card className="p-4">
                    <div className="text-2xl font-bold">{analytics.summary.avg_processing_time}초</div>
                    <div className="text-sm text-muted-foreground">평균 처리 시간</div>
                  </Card>
                  <Card className="p-4">
                    <div className="text-2xl font-bold">{analytics.summary.avg_user_satisfaction}/5</div>
                    <div className="text-sm text-muted-foreground">사용자 만족도</div>
                  </Card>
                </div>
                
                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-4">전략 사용 분포</h3>
                  <div className="space-y-3">
                    {Object.entries(analytics.strategy_distribution).map(([strategy, percentage]) => (
                      <div key={strategy} className="flex items-center justify-between">
                        <span className="text-sm">{strategy}</span>
                        <div className="flex items-center gap-2">
                          <Progress value={percentage as number} className="w-20 h-2" />
                          <span className="text-sm font-medium">{percentage as number}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
                
                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-4">최적화 인사이트</h3>
                  <ul className="space-y-2">
                    {analytics.optimization_insights.map((insight: string, index: number) => (
                      <li key={index} className="flex items-start gap-2 text-sm">
                        <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <span>{insight}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              </div>
            ) : (
              <div className="text-center py-12">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-muted-foreground">분석 데이터를 로딩 중...</p>
              </div>
            )}
          </TabsContent>
          
          <TabsContent value="predictions" className="space-y-4">
            {predictions ? (
              <div className="space-y-6">
                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    24시간 성능 예측
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <div className="text-2xl font-bold">{predictions.confidence * 100}%</div>
                      <div className="text-sm text-muted-foreground">예측 신뢰도</div>
                    </div>
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <div className="text-2xl font-bold">{predictions.forecast_period}</div>
                      <div className="text-sm text-muted-foreground">예측 기간</div>
                    </div>
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <div className="text-2xl font-bold">{predictions.model_info.accuracy * 100}%</div>
                      <div className="text-sm text-muted-foreground">모델 정확도</div>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <h4 className="font-medium">시간대별 예측:</h4>
                    <div className="grid gap-2 max-h-60 overflow-y-auto">
                      {predictions.predictions.slice(0, 12).map((pred: any, index: number) => (
                        <div key={index} className="flex items-center justify-between p-2 border rounded text-sm">
                          <span>{pred.hour}시간 후</span>
                          <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                              <span>부하:</span>
                              <Progress value={pred.predicted_load * 100} className="w-16 h-2" />
                              <span>{(pred.predicted_load * 100).toFixed(0)}%</span>
                            </div>
                            <Badge variant="outline">{pred.recommended_strategy}</Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </Card>
                
                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-4">추천사항</h3>
                  <ul className="space-y-2">
                    {predictions.recommendations.map((rec: string, index: number) => (
                      <li key={index} className="flex items-start gap-2 text-sm">
                        <Lightbulb className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              </div>
            ) : (
              <div className="text-center py-12">
                <TrendingUp className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-muted-foreground">예측 데이터를 로딩 중...</p>
              </div>
            )}
          </TabsContent>
          
          <TabsContent value="system" className="space-y-4">
            {systemMetrics ? (
              <div className="grid gap-6">
                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Activity className="h-5 w-5" />
                    시스템 상태
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium mb-3">예측 모델 상태</h4>
                      <div className="space-y-2">
                        {Object.entries(systemMetrics.prediction_models || {}).map(([name, model]: [string, any]) => (
                          <div key={name} className="flex items-center justify-between p-2 border rounded text-sm">
                            <span>{name}</span>
                            <div className="flex items-center gap-2">
                              <Badge variant={model.status === 'active' ? 'default' : 'secondary'}>
                                {model.status}
                              </Badge>
                              <span>{(model.accuracy * 100).toFixed(0)}%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-3">서비스 상태</h4>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between p-2 border rounded text-sm">
                          <span>성능 히스토리</span>
                          <Badge variant="outline">{systemMetrics.performance_history_size}개</Badge>
                        </div>
                        <div className="flex items-center justify-between p-2 border rounded text-sm">
                          <span>라우팅 패턴</span>
                          <Badge variant={systemMetrics.routing_patterns_loaded ? 'default' : 'secondary'}>
                            {systemMetrics.routing_patterns_loaded ? '로드됨' : '로드 안됨'}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between p-2 border rounded text-sm">
                          <span>Gemini 서비스</span>
                          <Badge variant={systemMetrics.gemini_service_available ? 'default' : 'destructive'}>
                            {systemMetrics.gemini_service_available ? '사용 가능' : '사용 불가'}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between p-2 border rounded text-sm">
                          <span>Auto-optimizer</span>
                          <Badge variant={systemMetrics.auto_optimizer_available ? 'default' : 'destructive'}>
                            {systemMetrics.auto_optimizer_available ? '사용 가능' : '사용 불가'}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>
              </div>
            ) : (
              <div className="text-center py-12">
                <Activity className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-muted-foreground">시스템 지표를 로딩 중...</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}