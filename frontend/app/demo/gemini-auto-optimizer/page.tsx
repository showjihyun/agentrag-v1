'use client';

/**
 * Gemini Auto-optimizer Demo Page
 * AI 기반 자동 최적화 데모 및 테스트 페이지
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import GeminiAutoOptimizerBlock from '@/components/agent-builder/blocks/GeminiAutoOptimizerBlock';
import {
  Wand2,
  Sparkles,
  Target,
  TrendingUp,
  Clock,
  DollarSign,
  Brain,
  Lightbulb,
  BarChart3,
  Settings,
  Zap,
  CheckCircle,
  AlertCircle,
  Info,
  ArrowRight,
  Play,
  Pause,
  RotateCcw
} from 'lucide-react';

interface DemoScenario {
  id: string;
  title: string;
  description: string;
  profile: any;
  expectedResults: {
    model: string;
    analysis_type: string;
    processing_time: string;
    accuracy: string;
    cost: string;
  };
  reasoning: string;
}

const DEMO_SCENARIOS: DemoScenario[] = [
  {
    id: 'educational',
    title: '교육 비디오 최적화',
    description: '온라인 강의 비디오의 정확한 분석이 필요한 시나리오',
    profile: {
      content_type: 'educational',
      media_complexity: 'moderate',
      file_size_mb: 45.2,
      duration_seconds: 1200,
      has_audio: true,
      user_priority: 'accuracy_first',
      min_accuracy_threshold: 0.92,
      batch_size: 1,
      is_realtime: false,
      user_experience_level: 'intermediate'
    },
    expectedResults: {
      model: 'gemini-1.5-pro',
      analysis_type: 'comprehensive',
      processing_time: '65-80초',
      accuracy: '94%',
      cost: '$0.12'
    },
    reasoning: '교육 콘텐츠는 정확도가 매우 중요하므로 Pro 모델과 종합 분석을 추천합니다.'
  },
  {
    id: 'marketing',
    title: '마케팅 비디오 빠른 분석',
    description: '소셜미디어용 짧은 마케팅 비디오의 빠른 처리',
    profile: {
      content_type: 'marketing',
      media_complexity: 'simple',
      file_size_mb: 12.8,
      duration_seconds: 60,
      has_audio: true,
      user_priority: 'speed_first',
      min_accuracy_threshold: 0.80,
      batch_size: 1,
      is_realtime: false,
      user_experience_level: 'beginner'
    },
    expectedResults: {
      model: 'gemini-1.5-flash',
      analysis_type: 'objects',
      processing_time: '8-12초',
      accuracy: '87%',
      cost: '$0.02'
    },
    reasoning: '마케팅 콘텐츠는 빠른 처리가 우선이므로 Flash 모델과 객체 분석을 추천합니다.'
  },
  {
    id: 'batch',
    title: '대량 배치 처리',
    description: '여러 비즈니스 비디오를 동시에 처리하는 시나리오',
    profile: {
      content_type: 'business',
      media_complexity: 'moderate',
      file_size_mb: 25.0,
      duration_seconds: 300,
      has_audio: true,
      user_priority: 'cost_efficient',
      min_accuracy_threshold: 0.85,
      batch_size: 8,
      is_realtime: false,
      user_experience_level: 'expert'
    },
    expectedResults: {
      model: 'gemini-1.5-flash',
      analysis_type: 'summary',
      processing_time: '15-20분 (전체)',
      accuracy: '85%',
      cost: '$0.18 (전체)'
    },
    reasoning: '배치 처리 시 비용 효율성을 위해 Flash 모델과 요약 분석을 추천합니다.'
  },
  {
    id: 'realtime',
    title: '실시간 처리',
    description: '라이브 스트림이나 실시간 분석이 필요한 시나리오',
    profile: {
      content_type: 'security',
      media_complexity: 'complex',
      file_size_mb: 35.0,
      duration_seconds: 180,
      has_audio: false,
      user_priority: 'speed_first',
      min_accuracy_threshold: 0.88,
      batch_size: 1,
      is_realtime: true,
      user_experience_level: 'expert'
    },
    expectedResults: {
      model: 'gemini-1.5-flash',
      analysis_type: 'objects',
      processing_time: '5-8초',
      accuracy: '89%',
      cost: '$0.04'
    },
    reasoning: '실시간 처리가 필요하므로 Flash 모델과 최소 프레임 수를 추천합니다.'
  }
];

export default function GeminiAutoOptimizerDemo() {
  const { toast } = useToast();
  const [activeScenario, setActiveScenario] = useState<DemoScenario | null>(null);
  const [isRunningDemo, setIsRunningDemo] = useState(false);
  const [demoProgress, setDemoProgress] = useState(0);
  const [demoResults, setDemoResults] = useState<any>(null);
  const [systemStats, setSystemStats] = useState<any>(null);

  useEffect(() => {
    loadSystemStats();
  }, []);

  const loadSystemStats = async () => {
    try {
      const response = await fetch('/api/agent-builder/gemini-auto-optimizer/stats');
      const data = await response.json();
      if (data.success) {
        setSystemStats(data.stats);
      }
    } catch (error) {
      console.error('Failed to load system stats:', error);
    }
  };

  const runScenarioDemo = async (scenario: DemoScenario) => {
    setActiveScenario(scenario);
    setIsRunningDemo(true);
    setDemoProgress(0);
    setDemoResults(null);

    try {
      // 진행률 시뮬레이션
      const progressInterval = setInterval(() => {
        setDemoProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + Math.random() * 15;
        });
      }, 200);

      // API 호출
      const response = await fetch('/api/agent-builder/gemini-auto-optimizer/optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(scenario.profile)
      });

      const data = await response.json();
      
      clearInterval(progressInterval);
      setDemoProgress(100);

      if (data.success) {
        setDemoResults(data.recommendation);
        toast({
          title: '🎉 데모 완료!',
          description: `${scenario.title} 최적화가 완료되었습니다.`,
        });
      } else {
        throw new Error(data.error || 'Optimization failed');
      }
    } catch (error) {
      console.error('Demo failed:', error);
      toast({
        title: '❌ 데모 실패',
        description: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.',
        variant: 'destructive'
      });
    } finally {
      setIsRunningDemo(false);
    }
  };

  const resetDemo = () => {
    setActiveScenario(null);
    setDemoResults(null);
    setDemoProgress(0);
    setIsRunningDemo(false);
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500">
            <Wand2 className="h-8 w-8 text-white" />
          </div>
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              Gemini Auto-optimizer
            </h1>
            <p className="text-xl text-muted-foreground mt-2">
              AI 기반 자동 최적화 및 전략 선택 데모
            </p>
          </div>
        </div>
        
        <div className="flex items-center justify-center gap-6 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Brain className="h-4 w-4" />
            <span>AI 기반 분석</span>
          </div>
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4" />
            <span>5가지 최적화 전략</span>
          </div>
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4" />
            <span>실시간 추천</span>
          </div>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            <span>성능 예측</span>
          </div>
        </div>
      </div>

      <Tabs defaultValue="scenarios" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="scenarios" className="flex items-center gap-2">
            <Play className="h-4 w-4" />
            시나리오 데모
          </TabsTrigger>
          <TabsTrigger value="interactive" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            인터랙티브 테스트
          </TabsTrigger>
          <TabsTrigger value="stats" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            시스템 통계
          </TabsTrigger>
          <TabsTrigger value="guide" className="flex items-center gap-2">
            <Lightbulb className="h-4 w-4" />
            사용 가이드
          </TabsTrigger>
        </TabsList>

        <TabsContent value="scenarios" className="space-y-6">
          {/* 시나리오 선택 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {DEMO_SCENARIOS.map((scenario) => (
              <Card key={scenario.id} className="cursor-pointer hover:shadow-lg transition-all">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>{scenario.title}</span>
                    <Badge variant="outline">
                      {scenario.profile.user_priority}
                    </Badge>
                  </CardTitle>
                  <CardDescription>{scenario.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">파일 크기:</span>
                        <span className="ml-2">{scenario.profile.file_size_mb}MB</span>
                      </div>
                      <div>
                        <span className="font-medium">길이:</span>
                        <span className="ml-2">{Math.floor(scenario.profile.duration_seconds / 60)}분</span>
                      </div>
                      <div>
                        <span className="font-medium">복잡도:</span>
                        <span className="ml-2">{scenario.profile.media_complexity}</span>
                      </div>
                      <div>
                        <span className="font-medium">배치:</span>
                        <span className="ml-2">{scenario.profile.batch_size}개</span>
                      </div>
                    </div>
                    
                    <div className="pt-2 border-t">
                      <p className="text-sm font-medium mb-2">예상 결과:</p>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div className="text-center p-2 bg-muted rounded">
                          <div className="font-medium">{scenario.expectedResults.processing_time}</div>
                          <div className="text-muted-foreground">처리 시간</div>
                        </div>
                        <div className="text-center p-2 bg-muted rounded">
                          <div className="font-medium">{scenario.expectedResults.accuracy}</div>
                          <div className="text-muted-foreground">정확도</div>
                        </div>
                        <div className="text-center p-2 bg-muted rounded">
                          <div className="font-medium">{scenario.expectedResults.cost}</div>
                          <div className="text-muted-foreground">비용</div>
                        </div>
                      </div>
                    </div>
                    
                    <Button
                      onClick={() => runScenarioDemo(scenario)}
                      disabled={isRunningDemo}
                      className="w-full gap-2"
                    >
                      {isRunningDemo && activeScenario?.id === scenario.id ? (
                        <>
                          <Pause className="h-4 w-4" />
                          최적화 중...
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4" />
                          데모 실행
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* 진행 상황 */}
          {isRunningDemo && activeScenario && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5 animate-pulse" />
                  {activeScenario.title} 최적화 진행 중...
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Progress value={demoProgress} className="w-full" />
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>AI가 최적 설정을 분석하고 있습니다...</span>
                    <span>{Math.round(demoProgress)}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 결과 표시 */}
          {demoResults && activeScenario && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    {activeScenario.title} 최적화 완료
                  </CardTitle>
                  <Button variant="outline" size="sm" onClick={resetDemo}>
                    <RotateCcw className="h-4 w-4 mr-2" />
                    다시 시작
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold mb-3">추천 설정</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>모델:</span>
                        <Badge variant="outline">{demoResults.model}</Badge>
                      </div>
                      <div className="flex justify-between">
                        <span>분석 유형:</span>
                        <Badge variant="outline">{demoResults.analysis_type}</Badge>
                      </div>
                      <div className="flex justify-between">
                        <span>최대 프레임:</span>
                        <span>{demoResults.max_frames}개</span>
                      </div>
                      <div className="flex justify-between">
                        <span>온도:</span>
                        <span>{demoResults.temperature}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold mb-3">성능 예측</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span>처리 시간:</span>
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span>{demoResults.performance_prediction.estimated_processing_time.toFixed(1)}초</span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>정확도:</span>
                        <div className="flex items-center gap-2">
                          <TrendingUp className="h-4 w-4 text-muted-foreground" />
                          <span>{(demoResults.performance_prediction.estimated_accuracy * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>비용:</span>
                        <div className="flex items-center gap-2">
                          <DollarSign className="h-4 w-4 text-muted-foreground" />
                          <span>${demoResults.performance_prediction.estimated_cost.toFixed(3)}</span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>신뢰도:</span>
                        <div className="flex items-center gap-2">
                          <Progress 
                            value={demoResults.performance_prediction.confidence_score * 100} 
                            className="w-16 h-2"
                          />
                          <span>{(demoResults.performance_prediction.confidence_score * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="mt-6 p-4 bg-muted rounded-lg">
                  <h4 className="font-medium mb-2 flex items-center gap-2">
                    <Brain className="h-4 w-4" />
                    AI 추천 근거
                  </h4>
                  <p className="text-sm text-muted-foreground">{demoResults.reasoning}</p>
                </div>
                
                {demoResults.optimization_tips && demoResults.optimization_tips.length > 0 && (
                  <div className="mt-4">
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <Lightbulb className="h-4 w-4" />
                      최적화 팁
                    </h4>
                    <ul className="space-y-1">
                      {demoResults.optimization_tips.map((tip: string, index: number) => (
                        <li key={index} className="flex items-start gap-2 text-sm">
                          <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span>{tip}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="interactive">
          <Card>
            <CardHeader>
              <CardTitle>인터랙티브 최적화 테스트</CardTitle>
              <CardDescription>
                직접 설정을 입력하고 AI 최적화를 체험해보세요
              </CardDescription>
            </CardHeader>
            <CardContent>
              <GeminiAutoOptimizerBlock
                blockId="demo-optimizer"
                onExecute={(result) => {
                  toast({
                    title: '✨ 최적화 완료',
                    description: '인터랙티브 테스트가 성공적으로 완료되었습니다!',
                  });
                }}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="stats">
          <div className="grid gap-6">
            {systemStats ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium">시스템 상태</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-green-600">
                        {systemStats.system_health?.status || 'Healthy'}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        최적화 엔진 정상 작동
                      </p>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium">총 최적화 수행</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {systemStats.usage_statistics?.total_optimizations || 0}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        성공률: {systemStats.usage_statistics?.successful_optimizations || 0}건
                      </p>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium">평균 신뢰도</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {((systemStats.usage_statistics?.average_confidence || 0.85) * 100).toFixed(0)}%
                      </div>
                      <p className="text-xs text-muted-foreground">
                        AI 추천 신뢰도
                      </p>
                    </CardContent>
                  </Card>
                </div>
                
                <Card>
                  <CardHeader>
                    <CardTitle>인기 설정</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {systemStats.popular_configurations?.map((config: any, index: number) => (
                        <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                          <div className="flex items-center gap-3">
                            <Badge variant="outline">{config.model}</Badge>
                            <span className="text-sm">{config.analysis_type}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Progress value={config.usage_percentage} className="w-20 h-2" />
                            <span className="text-sm font-medium">{config.usage_percentage}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card>
                <CardContent className="text-center py-12">
                  <BarChart3 className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">통계 데이터를 로딩 중...</p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="guide">
          <div className="grid gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="h-5 w-5" />
                  Auto-optimizer 사용 가이드
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h3 className="font-semibold mb-3">1. 최적화 전략 선택</h3>
                  <div className="grid gap-3">
                    <div className="flex items-start gap-3 p-3 border rounded-lg">
                      <Zap className="h-5 w-5 text-blue-500 mt-0.5" />
                      <div>
                        <div className="font-medium">속도 우선 (Speed First)</div>
                        <div className="text-sm text-muted-foreground">실시간 처리나 대량 배치에 적합</div>
                      </div>
                    </div>
                    <div className="flex items-start gap-3 p-3 border rounded-lg">
                      <Target className="h-5 w-5 text-green-500 mt-0.5" />
                      <div>
                        <div className="font-medium">정확도 우선 (Accuracy First)</div>
                        <div className="text-sm text-muted-foreground">중요한 문서나 의료/법률 분야에 적합</div>
                      </div>
                    </div>
                    <div className="flex items-start gap-3 p-3 border rounded-lg">
                      <TrendingUp className="h-5 w-5 text-purple-500 mt-0.5" />
                      <div>
                        <div className="font-medium">균형 (Balanced)</div>
                        <div className="text-sm text-muted-foreground">일반적인 비즈니스 용도에 적합</div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="font-semibold mb-3">2. 콘텐츠 유형별 최적화</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between p-2 border rounded">
                      <span>교육 콘텐츠</span>
                      <span className="text-muted-foreground">정확도 중심, 종합 분석</span>
                    </div>
                    <div className="flex justify-between p-2 border rounded">
                      <span>마케팅 콘텐츠</span>
                      <span className="text-muted-foreground">속도 중심, 객체 인식</span>
                    </div>
                    <div className="flex justify-between p-2 border rounded">
                      <span>보안 콘텐츠</span>
                      <span className="text-muted-foreground">높은 정확도, 객체 탐지</span>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="font-semibold mb-3">3. 성능 최적화 팁</h3>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-start gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500 mt-0.5" />
                      <span>파일 크기가 클수록 프레임 수를 줄여 처리 시간 단축</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500 mt-0.5" />
                      <span>배치 처리 시 Flash 모델 사용으로 전체 시간 단축</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500 mt-0.5" />
                      <span>실시간 처리가 필요한 경우 프레임 수를 15개 이하로 제한</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500 mt-0.5" />
                      <span>오디오가 없는 비디오는 시각적 분석에 집중</span>
                    </li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}