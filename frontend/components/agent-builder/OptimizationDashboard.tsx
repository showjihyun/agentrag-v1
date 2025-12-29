'use client';

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '@/components/ui/alert';
import {
  Zap,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  Clock,
  DollarSign,
  BarChart3,
  Target,
  Lightbulb,
  Wrench,
  Shield,
  Cpu,
  RefreshCw,
  Play,
  Settings,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI, type OptimizationSuggestion, type WorkflowAnalysis } from '@/lib/api/agent-builder';

interface OptimizationDashboardProps {
  workflowId: string;
  onOptimizationApplied?: () => void;
}

export function OptimizationDashboard({
  workflowId,
  onOptimizationApplied,
}: OptimizationDashboardProps) {
  const [selectedSuggestions, setSelectedSuggestions] = useState<string[]>([]);
  const [showDetails, setShowDetails] = useState<Record<string, boolean>>({});
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch optimization analysis
  const {
    data: analysisData,
    isLoading: analysisLoading,
    error: analysisError,
    refetch: refetchAnalysis,
  } = useQuery({
    queryKey: ['optimization-analysis', workflowId],
    queryFn: () => agentBuilderAPI.getOptimizationAnalysis(workflowId),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Fetch recommendations
  const {
    data: recommendationsData,
    isLoading: recommendationsLoading,
    refetch: refetchRecommendations,
  } = useQuery({
    queryKey: ['optimization-recommendations', workflowId],
    queryFn: () => agentBuilderAPI.getOptimizationRecommendations(workflowId, 10),
  });

  // Fetch health score
  const { data: healthScore } = useQuery({
    queryKey: ['workflow-health', workflowId],
    queryFn: () => agentBuilderAPI.getWorkflowHealthScore(workflowId),
  });

  // Fetch optimization insights
  const { data: insights } = useQuery({
    queryKey: ['optimization-insights', workflowId],
    queryFn: () => agentBuilderAPI.getOptimizationInsights(workflowId),
  });

  // Apply optimizations mutation
  const applyOptimizationsMutation = useMutation({
    mutationFn: ({ suggestionIds, autoApply }: { suggestionIds: string[]; autoApply: boolean }) =>
      agentBuilderAPI.applyOptimizations(workflowId, suggestionIds, autoApply),
    onSuccess: (data) => {
      toast({
        title: '최적화 적용 완료',
        description: data.message,
      });
      setSelectedSuggestions([]);
      queryClient.invalidateQueries({ queryKey: ['optimization-analysis', workflowId] });
      queryClient.invalidateQueries({ queryKey: ['optimization-recommendations', workflowId] });
      onOptimizationApplied?.();
    },
    onError: (error) => {
      toast({
        title: '최적화 적용 실패',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  const analysis = analysisData?.analysis;
  const recommendations = recommendationsData?.recommendations || [];

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low':
        return 'text-green-600 bg-green-50 border-green-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'destructive';
      case 'medium':
        return 'default';
      case 'low':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'performance':
        return <Zap className="w-4 h-4" />;
      case 'cost':
        return <DollarSign className="w-4 h-4" />;
      case 'reliability':
        return <Shield className="w-4 h-4" />;
      case 'resource':
        return <Cpu className="w-4 h-4" />;
      default:
        return <Settings className="w-4 h-4" />;
    }
  };

  const handleSuggestionToggle = (suggestionId: string) => {
    setSelectedSuggestions(prev =>
      prev.includes(suggestionId)
        ? prev.filter(id => id !== suggestionId)
        : [...prev, suggestionId]
    );
  };

  const handleApplyOptimizations = (autoApply: boolean = false) => {
    if (selectedSuggestions.length === 0) {
      toast({
        title: '선택된 최적화 없음',
        description: '적용할 최적화 제안을 선택해주세요.',
        variant: 'destructive',
      });
      return;
    }

    applyOptimizationsMutation.mutate({
      suggestionIds: selectedSuggestions,
      autoApply,
    });
  };

  const toggleDetails = (suggestionId: string) => {
    setShowDetails(prev => ({
      ...prev,
      [suggestionId]: !prev[suggestionId],
    }));
  };

  if (analysisLoading || recommendationsLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="w-6 h-6 animate-spin mr-2" />
        <span>최적화 분석 중...</span>
      </div>
    );
  }

  if (analysisError) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>분석 오류</AlertTitle>
        <AlertDescription>
          워크플로우 최적화 분석을 불러올 수 없습니다. 다시 시도해주세요.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with refresh button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">워크플로우 최적화</h2>
          <p className="text-gray-600">성능, 비용, 안정성을 개선하기 위한 지능적 제안</p>
        </div>
        <Button
          variant="outline"
          onClick={() => {
            refetchAnalysis();
            refetchRecommendations();
          }}
          disabled={analysisLoading}
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${analysisLoading ? 'animate-spin' : ''}`} />
          새로고침
        </Button>
      </div>

      {/* Health Score Overview */}
      {healthScore && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Target className="w-4 h-4" />
                전체 점수
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(healthScore.overall_score * 100).toFixed(0)}
              </div>
              <Progress value={healthScore.overall_score * 100} className="mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Zap className="w-4 h-4" />
                성능
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(healthScore.performance_score * 100).toFixed(0)}
              </div>
              <Progress value={healthScore.performance_score * 100} className="mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Shield className="w-4 h-4" />
                안정성
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(healthScore.reliability_score * 100).toFixed(0)}
              </div>
              <Progress value={healthScore.reliability_score * 100} className="mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <DollarSign className="w-4 h-4" />
                비용 효율성
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(healthScore.cost_efficiency_score * 100).toFixed(0)}
              </div>
              <Progress value={healthScore.cost_efficiency_score * 100} className="mt-2" />
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="recommendations" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="recommendations">제안사항</TabsTrigger>
          <TabsTrigger value="analysis">상세 분석</TabsTrigger>
          <TabsTrigger value="insights">인사이트</TabsTrigger>
          <TabsTrigger value="bottlenecks">병목 지점</TabsTrigger>
        </TabsList>

        {/* Recommendations Tab */}
        <TabsContent value="recommendations" className="space-y-4">
          {recommendations.length === 0 ? (
            <Card>
              <CardContent className="flex items-center justify-center py-8">
                <div className="text-center">
                  <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-4" />
                  <h3 className="text-lg font-medium">최적화 완료!</h3>
                  <p className="text-gray-600">현재 워크플로우는 최적 상태입니다.</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Action buttons */}
              <div className="flex items-center gap-4">
                <div className="text-sm text-gray-600">
                  {selectedSuggestions.length}개 선택됨
                </div>
                <Button
                  onClick={() => handleApplyOptimizations(false)}
                  disabled={selectedSuggestions.length === 0 || applyOptimizationsMutation.isPending}
                >
                  <Wrench className="w-4 h-4 mr-2" />
                  선택된 최적화 적용
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleApplyOptimizations(true)}
                  disabled={selectedSuggestions.length === 0 || applyOptimizationsMutation.isPending}
                >
                  <Play className="w-4 h-4 mr-2" />
                  자동 적용
                </Button>
              </div>

              {/* Recommendations list */}
              <div className="space-y-4">
                {recommendations.map((suggestion, index) => (
                  <Card key={index} className="relative">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <input
                            type="checkbox"
                            checked={selectedSuggestions.includes(`suggestion-${index}`)}
                            onChange={() => handleSuggestionToggle(`suggestion-${index}`)}
                            className="mt-1"
                          />
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              {getTypeIcon(suggestion.type)}
                              <CardTitle className="text-lg">{suggestion.title}</CardTitle>
                              <Badge variant={getPriorityColor(suggestion.priority)}>
                                {suggestion.priority} 우선순위
                              </Badge>
                              <Badge className={getImpactColor(suggestion.impact)}>
                                {suggestion.impact} 임팩트
                              </Badge>
                            </div>
                            <p className="text-gray-600">{suggestion.description}</p>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleDetails(`suggestion-${index}`)}
                        >
                          {showDetails[`suggestion-${index}`] ? '간단히' : '자세히'}
                        </Button>
                      </div>
                    </CardHeader>

                    {showDetails[`suggestion-${index}`] && (
                      <CardContent className="pt-0">
                        <Separator className="mb-4" />
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                          {suggestion.estimated_improvement && (
                            <div>
                              <span className="font-medium">예상 개선율:</span>
                              <div className="text-green-600 font-medium">
                                {(suggestion.estimated_improvement * 100).toFixed(1)}%
                              </div>
                            </div>
                          )}
                          {suggestion.confidence_score && (
                            <div>
                              <span className="font-medium">신뢰도:</span>
                              <div className="font-medium">
                                {(suggestion.confidence_score * 100).toFixed(0)}%
                              </div>
                            </div>
                          )}
                          {suggestion.implementation_effort && (
                            <div>
                              <span className="font-medium">구현 난이도:</span>
                              <div className="font-medium">{suggestion.implementation_effort}</div>
                            </div>
                          )}
                        </div>
                        {suggestion.action && (
                          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                            <div className="font-medium text-blue-900 mb-1">권장 조치:</div>
                            <div className="text-blue-800">{suggestion.action}</div>
                          </div>
                        )}
                      </CardContent>
                    )}
                  </Card>
                ))}
              </div>
            </>
          )}
        </TabsContent>

        {/* Analysis Tab */}
        <TabsContent value="analysis" className="space-y-4">
          {analysis && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="w-5 h-5" />
                    실행 통계
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between">
                    <span>총 실행 횟수:</span>
                    <span className="font-medium">{analysis.execution_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>성공률:</span>
                    <span className="font-medium">{(analysis.success_rate * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>평균 실행 시간:</span>
                    <span className="font-medium">{(analysis.average_duration_ms / 1000).toFixed(1)}초</span>
                  </div>
                  <div className="flex justify-between">
                    <span>최적화 점수:</span>
                    <span className="font-medium">{(analysis.optimization_score * 100).toFixed(0)}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Cpu className="w-5 h-5" />
                    리소스 사용량
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between">
                    <span>평균 토큰/실행:</span>
                    <span className="font-medium">
                      {analysis.resource_usage.avg_tokens_per_execution.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>평균 메모리/실행:</span>
                    <span className="font-medium">
                      {analysis.resource_usage.avg_memory_mb_per_execution.toFixed(1)}MB
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>리소스 효율성:</span>
                    <span className="font-medium">
                      {(analysis.resource_usage.resource_efficiency_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <DollarSign className="w-5 h-5" />
                    비용 분석
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between">
                    <span>총 비용:</span>
                    <span className="font-medium">${analysis.cost_analysis.total_cost.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>평균 비용/실행:</span>
                    <span className="font-medium">${analysis.cost_analysis.avg_cost_per_execution.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>일평균 비용:</span>
                    <span className="font-medium">${analysis.cost_analysis.avg_daily_cost.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>비용 트렌드:</span>
                    <span className={`font-medium flex items-center gap-1 ${
                      analysis.cost_analysis.cost_trend === 'increasing' ? 'text-red-600' :
                      analysis.cost_analysis.cost_trend === 'decreasing' ? 'text-green-600' :
                      'text-gray-600'
                    }`}>
                      {analysis.cost_analysis.cost_trend === 'increasing' && <TrendingUp className="w-4 h-4" />}
                      {analysis.cost_analysis.cost_trend === 'decreasing' && <TrendingDown className="w-4 h-4" />}
                      {analysis.cost_analysis.cost_trend}
                    </span>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Insights Tab */}
        <TabsContent value="insights" className="space-y-4">
          {insights && (
            <div className="space-y-6">
              {/* Critical Issues */}
              {insights.critical_issues.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-red-600">
                      <AlertTriangle className="w-5 h-5" />
                      긴급 해결 필요 ({insights.critical_issues.length}개)
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {insights.critical_issues.map((issue, index) => (
                        <div key={index} className="p-3 border-l-4 border-red-500 bg-red-50">
                          <div className="font-medium text-red-900">{issue.title}</div>
                          <div className="text-red-700 text-sm mt-1">{issue.description}</div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Quick Wins */}
              {insights.quick_wins.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-green-600">
                      <Lightbulb className="w-5 h-5" />
                      빠른 개선 ({insights.quick_wins.length}개)
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {insights.quick_wins.map((win, index) => (
                        <div key={index} className="p-3 border-l-4 border-green-500 bg-green-50">
                          <div className="font-medium text-green-900">{win.title}</div>
                          <div className="text-green-700 text-sm mt-1">{win.description}</div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Potential Savings */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <DollarSign className="w-5 h-5 text-green-600" />
                      비용 절감 잠재력
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-green-600">
                      {(insights.cost_savings_potential * 100).toFixed(0)}%
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      최적화 적용 시 예상 비용 절감률
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Zap className="w-5 h-5 text-blue-600" />
                      성능 개선 잠재력
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-blue-600">
                      {(insights.performance_improvement_potential * 100).toFixed(0)}%
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      최적화 적용 시 예상 성능 향상률
                    </p>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}
        </TabsContent>

        {/* Bottlenecks Tab */}
        <TabsContent value="bottlenecks" className="space-y-4">
          {analysis?.bottlenecks && analysis.bottlenecks.length > 0 ? (
            <div className="space-y-4">
              {analysis.bottlenecks.map((bottleneck, index) => (
                <Card key={index}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5 text-yellow-600" />
                        {bottleneck.agent_name}
                      </CardTitle>
                      <Badge variant="outline">
                        심각도: {(bottleneck.severity * 100).toFixed(0)}%
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="font-medium">병목 유형:</span>
                          <div className="mt-1">{bottleneck.bottleneck_type}</div>
                        </div>
                        <div>
                          <span className="font-medium">발생 빈도:</span>
                          <div className="mt-1">{(bottleneck.frequency * 100).toFixed(0)}%</div>
                        </div>
                        <div>
                          <span className="font-medium">전체 시간 비중:</span>
                          <div className="mt-1">{(bottleneck.impact_on_total_time * 100).toFixed(1)}%</div>
                        </div>
                      </div>
                      
                      <div>
                        <span className="font-medium">해결 방안:</span>
                        <ul className="mt-2 space-y-1">
                          {bottleneck.suggested_fixes.map((fix, fixIndex) => (
                            <li key={fixIndex} className="text-sm text-gray-600 flex items-start gap-2">
                              <span className="text-blue-500 mt-1">•</span>
                              {fix}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center py-8">
                <div className="text-center">
                  <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-4" />
                  <h3 className="text-lg font-medium">병목 지점 없음</h3>
                  <p className="text-gray-600">현재 워크플로우에서 주요 병목 지점이 발견되지 않았습니다.</p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}