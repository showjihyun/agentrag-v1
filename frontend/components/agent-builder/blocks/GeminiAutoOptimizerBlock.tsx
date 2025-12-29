'use client';

/**
 * Gemini Auto-optimizer Block
 * AI 기반 자동 최적화 및 전략 선택 블록
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import {
  Sparkles,
  Settings,
  Zap,
  Target,
  TrendingUp,
  Clock,
  DollarSign,
  Brain,
  Lightbulb,
  CheckCircle,
  AlertCircle,
  Info,
  Loader2,
  RefreshCw,
  BarChart3,
  Sliders,
  Wand2,
  Star,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react';

interface GeminiAutoOptimizerBlockProps {
  blockId: string;
  config?: any;
  onConfigChange?: (config: any) => void;
  onExecute?: (result: any) => void;
  isExecuting?: boolean;
}

interface OptimizationProfile {
  content_type?: string;
  media_complexity?: string;
  file_size_mb: number;
  duration_seconds: number;
  has_audio: boolean;
  user_priority: string;
  max_processing_time?: number;
  min_accuracy_threshold: number;
  budget_constraint?: number;
  batch_size: number;
  is_realtime: boolean;
  user_experience_level: string;
}

interface OptimizationRecommendation {
  analysis_type: string;
  model: string;
  temperature: number;
  max_tokens: number;
  frame_sampling: string;
  max_frames: number;
  fusion_strategy?: string;
  performance_prediction: {
    estimated_processing_time: number;
    estimated_accuracy: number;
    estimated_cost: number;
    confidence_score: number;
  };
  reasoning: string;
  alternative_options: Array<{
    name: string;
    model: string;
    analysis_type: string;
    max_frames: number;
    estimated_time: number;
    estimated_accuracy: number;
    description: string;
  }>;
  optimization_tips: string[];
}

export default function GeminiAutoOptimizerBlock({
  blockId,
  config = {},
  onConfigChange,
  onExecute,
  isExecuting = false
}: GeminiAutoOptimizerBlockProps) {
  const { toast } = useToast();
  
  // State
  const [profile, setProfile] = useState<OptimizationProfile>({
    file_size_mb: 25,
    duration_seconds: 300,
    has_audio: true,
    user_priority: 'balanced',
    min_accuracy_threshold: 0.85,
    batch_size: 1,
    is_realtime: false,
    user_experience_level: 'intermediate'
  });
  
  const [recommendation, setRecommendation] = useState<OptimizationRecommendation | null>(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [strategies, setStrategies] = useState<any[]>([]);
  const [contentTypes, setContentTypes] = useState<any[]>([]);
  const [complexityLevels, setComplexityLevels] = useState<any[]>([]);
  const [examples, setExamples] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState('profile');
  const [userFeedback, setUserFeedback] = useState<'positive' | 'negative' | null>(null);
  
  // Load initial data
  useEffect(() => {
    loadStrategies();
    loadContentTypes();
    loadComplexityLevels();
    loadExamples();
  }, []);
  
  // Update config when profile changes
  useEffect(() => {
    if (onConfigChange) {
      onConfigChange({
        ...config,
        profile,
        recommendation,
        userFeedback
      });
    }
  }, [profile, recommendation, userFeedback, onConfigChange]);
  
  const loadStrategies = async () => {
    try {
      const response = await fetch('/api/agent-builder/gemini-auto-optimizer/strategies');
      const data = await response.json();
      if (data.success) {
        setStrategies(data.strategies);
      }
    } catch (error) {
      console.error('Failed to load strategies:', error);
    }
  };
  
  const loadContentTypes = async () => {
    try {
      const response = await fetch('/api/agent-builder/gemini-auto-optimizer/content-types');
      const data = await response.json();
      if (data.success) {
        setContentTypes(data.content_types);
      }
    } catch (error) {
      console.error('Failed to load content types:', error);
    }
  };
  
  const loadComplexityLevels = async () => {
    try {
      const response = await fetch('/api/agent-builder/gemini-auto-optimizer/complexity-levels');
      const data = await response.json();
      if (data.success) {
        setComplexityLevels(data.complexity_levels);
      }
    } catch (error) {
      console.error('Failed to load complexity levels:', error);
    }
  };
  
  const loadExamples = async () => {
    try {
      const response = await fetch('/api/agent-builder/gemini-auto-optimizer/examples');
      const data = await response.json();
      if (data.success) {
        setExamples(data.examples);
      }
    } catch (error) {
      console.error('Failed to load examples:', error);
    }
  };
  
  const handleOptimize = async () => {
    setIsOptimizing(true);
    setActiveTab('results');
    
    try {
      const response = await fetch('/api/agent-builder/gemini-auto-optimizer/optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(profile)
      });
      
      const data = await response.json();
      
      if (data.success && data.recommendation) {
        setRecommendation(data.recommendation);
        toast({
          title: '✨ 최적화 완료',
          description: `${data.processing_time_seconds.toFixed(2)}초 만에 최적 설정을 찾았습니다!`,
        });
        
        // Execute with optimized settings if onExecute is provided
        if (onExecute) {
          onExecute({
            type: 'auto_optimization',
            profile,
            recommendation: data.recommendation,
            processing_time: data.processing_time_seconds
          });
        }
      } else {
        throw new Error(data.error || 'Optimization failed');
      }
    } catch (error) {
      console.error('Optimization failed:', error);
      toast({
        title: '❌ 최적화 실패',
        description: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.',
        variant: 'destructive'
      });
    } finally {
      setIsOptimizing(false);
    }
  };
  
  const handleFeedback = async (feedback: 'positive' | 'negative') => {
    if (!recommendation) return;
    
    setUserFeedback(feedback);
    
    try {
      await fetch('/api/agent-builder/gemini-auto-optimizer/record-performance', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          config: {
            profile,
            recommendation
          },
          actual_processing_time: recommendation.performance_prediction.estimated_processing_time,
          success: true,
          user_rating: feedback === 'positive' ? 5 : 2
        })
      });
      
      toast({
        title: feedback === 'positive' ? '👍 피드백 감사합니다!' : '👎 피드백이 기록되었습니다',
        description: '향후 최적화 개선에 활용하겠습니다.',
      });
    } catch (error) {
      console.error('Failed to record feedback:', error);
    }
  };
  
  const applyExample = (example: any) => {
    setProfile(prev => ({
      ...prev,
      ...example.scenario
    }));
    setActiveTab('profile');
    toast({
      title: '📋 예시 적용됨',
      description: `${example.title} 설정이 적용되었습니다.`,
    });
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
    <Card className="w-full max-w-4xl">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500">
            <Wand2 className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold">Gemini Auto-optimizer</h3>
            <p className="text-sm text-muted-foreground font-normal">
              AI 기반 자동 최적화 및 전략 선택
            </p>
          </div>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="profile" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              프로필
            </TabsTrigger>
            <TabsTrigger value="examples" className="flex items-center gap-2">
              <Lightbulb className="h-4 w-4" />
              예시
            </TabsTrigger>
            <TabsTrigger value="results" className="flex items-center gap-2">
              <Target className="h-4 w-4" />
              결과
            </TabsTrigger>
            <TabsTrigger value="stats" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              통계
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="profile" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* 기본 설정 */}
              <div className="space-y-4">
                <h4 className="font-semibold flex items-center gap-2">
                  <Sliders className="h-4 w-4" />
                  기본 설정
                </h4>
                
                <div className="space-y-3">
                  <div>
                    <Label htmlFor="content-type">콘텐츠 유형</Label>
                    <Select
                      value={profile.content_type || ''}
                      onValueChange={(value) => setProfile(prev => ({ ...prev, content_type: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="콘텐츠 유형 선택" />
                      </SelectTrigger>
                      <SelectContent>
                        {contentTypes.map(type => (
                          <SelectItem key={type.id} value={type.id}>
                            {type.name} - {type.description}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="complexity">미디어 복잡도</Label>
                    <Select
                      value={profile.media_complexity || ''}
                      onValueChange={(value) => setProfile(prev => ({ ...prev, media_complexity: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="복잡도 선택" />
                      </SelectTrigger>
                      <SelectContent>
                        {complexityLevels.map(level => (
                          <SelectItem key={level.id} value={level.id}>
                            {level.name} - {level.description}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="strategy">최적화 전략</Label>
                    <Select
                      value={profile.user_priority}
                      onValueChange={(value) => setProfile(prev => ({ ...prev, user_priority: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {strategies.map(strategy => (
                          <SelectItem key={strategy.id} value={strategy.id}>
                            {strategy.name} - {strategy.description}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
              
              {/* 파일 정보 */}
              <div className="space-y-4">
                <h4 className="font-semibold flex items-center gap-2">
                  <Info className="h-4 w-4" />
                  파일 정보
                </h4>
                
                <div className="space-y-3">
                  <div>
                    <Label htmlFor="file-size">파일 크기 (MB)</Label>
                    <Input
                      id="file-size"
                      type="number"
                      value={profile.file_size_mb}
                      onChange={(e) => setProfile(prev => ({ 
                        ...prev, 
                        file_size_mb: parseFloat(e.target.value) || 0 
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
                      value={profile.duration_seconds}
                      onChange={(e) => setProfile(prev => ({ 
                        ...prev, 
                        duration_seconds: parseFloat(e.target.value) || 0 
                      }))}
                      min="0"
                      step="1"
                    />
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="has-audio"
                      checked={profile.has_audio}
                      onChange={(e) => setProfile(prev => ({ 
                        ...prev, 
                        has_audio: e.target.checked 
                      }))}
                      className="rounded"
                    />
                    <Label htmlFor="has-audio">오디오 포함</Label>
                  </div>
                </div>
              </div>
            </div>
            
            {/* 고급 설정 */}
            <div className="space-y-4">
              <h4 className="font-semibold flex items-center gap-2">
                <Settings className="h-4 w-4" />
                고급 설정
              </h4>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="accuracy">최소 정확도 (%)</Label>
                  <Input
                    id="accuracy"
                    type="number"
                    value={Math.round(profile.min_accuracy_threshold * 100)}
                    onChange={(e) => setProfile(prev => ({ 
                      ...prev, 
                      min_accuracy_threshold: (parseFloat(e.target.value) || 85) / 100 
                    }))}
                    min="50"
                    max="100"
                    step="5"
                  />
                </div>
                
                <div>
                  <Label htmlFor="batch-size">배치 크기</Label>
                  <Input
                    id="batch-size"
                    type="number"
                    value={profile.batch_size}
                    onChange={(e) => setProfile(prev => ({ 
                      ...prev, 
                      batch_size: parseInt(e.target.value) || 1 
                    }))}
                    min="1"
                    max="20"
                  />
                </div>
                
                <div>
                  <Label htmlFor="max-time">최대 처리 시간 (초)</Label>
                  <Input
                    id="max-time"
                    type="number"
                    value={profile.max_processing_time || ''}
                    onChange={(e) => {
                      const value = e.target.value ? parseFloat(e.target.value) : undefined;
                      setProfile(prev => {
                        const newProfile = { ...prev };
                        if (value !== undefined) {
                          newProfile.max_processing_time = value;
                        } else {
                          delete newProfile.max_processing_time;
                        }
                        return newProfile;
                      });
                    }}
                    placeholder="제한 없음"
                    min="1"
                  />
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="realtime"
                    checked={profile.is_realtime}
                    onChange={(e) => setProfile(prev => ({ 
                      ...prev, 
                      is_realtime: e.target.checked 
                    }))}
                    className="rounded"
                  />
                  <Label htmlFor="realtime">실시간 처리</Label>
                </div>
                
                <div>
                  <Label htmlFor="experience">경험 수준</Label>
                  <Select
                    value={profile.user_experience_level}
                    onValueChange={(value) => setProfile(prev => ({ ...prev, user_experience_level: value }))}
                  >
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="beginner">초급</SelectItem>
                      <SelectItem value="intermediate">중급</SelectItem>
                      <SelectItem value="expert">고급</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
            
            {/* 최적화 실행 버튼 */}
            <div className="flex justify-center pt-4">
              <Button
                onClick={handleOptimize}
                disabled={isOptimizing || isExecuting}
                size="lg"
                className="gap-2"
              >
                {isOptimizing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    최적화 중...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    AI 최적화 실행
                  </>
                )}
              </Button>
            </div>
          </TabsContent>
          
          <TabsContent value="examples" className="space-y-4">
            <div className="grid gap-4">
              {examples.map((example, index) => (
                <Card key={index} className="p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h4 className="font-semibold">{example.title}</h4>
                      <p className="text-sm text-muted-foreground mt-1">
                        {example.scenario.content_type} • {example.scenario.user_priority}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => applyExample(example)}
                      className="gap-2"
                    >
                      <RefreshCw className="h-3 w-3" />
                      적용
                    </Button>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="font-medium mb-2">시나리오:</p>
                      <ul className="space-y-1 text-muted-foreground">
                        <li>• 파일 크기: {example.scenario.file_size_mb}MB</li>
                        <li>• 길이: {example.scenario.duration_seconds}초</li>
                        <li>• 전략: {example.scenario.user_priority}</li>
                      </ul>
                    </div>
                    
                    <div>
                      <p className="font-medium mb-2">예상 결과:</p>
                      <ul className="space-y-1 text-muted-foreground">
                        <li>• 처리 시간: {example.expected_results.processing_time}</li>
                        <li>• 정확도: {example.expected_results.accuracy}</li>
                        <li>• 비용: {example.expected_results.cost}</li>
                      </ul>
                    </div>
                  </div>
                  
                  <div className="mt-3 p-3 bg-muted rounded-lg">
                    <p className="text-sm">
                      <strong>추천 근거:</strong> {example.recommendation.reasoning}
                    </p>
                  </div>
                </Card>
              ))}
            </div>
          </TabsContent>
          
          <TabsContent value="results" className="space-y-6">
            {isOptimizing ? (
              <div className="text-center py-12">
                <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
                <h3 className="text-lg font-semibold mb-2">AI가 최적 설정을 분석 중입니다...</h3>
                <p className="text-muted-foreground">
                  콘텐츠 유형, 복잡도, 사용자 선호도를 종합하여 최적화하고 있습니다.
                </p>
              </div>
            ) : recommendation ? (
              <div className="space-y-6">
                {/* 추천 설정 */}
                <Card className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                      <Target className="h-5 w-5" />
                      추천 설정
                    </h3>
                    <Badge {...getConfidenceBadge(recommendation.performance_prediction.confidence_score)}>
                      신뢰도: {getConfidenceBadge(recommendation.performance_prediction.confidence_score).text}
                    </Badge>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="font-medium">모델:</span>
                        <Badge variant="outline">{recommendation.model}</Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-medium">분석 유형:</span>
                        <Badge variant="outline">{recommendation.analysis_type}</Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-medium">최대 프레임:</span>
                        <span>{recommendation.max_frames}개</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-medium">온도:</span>
                        <span>{recommendation.temperature}</span>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="font-medium">예상 처리 시간:</span>
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span>{recommendation.performance_prediction.estimated_processing_time.toFixed(1)}초</span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="font-medium">예상 정확도:</span>
                        <div className="flex items-center gap-2">
                          <TrendingUp className="h-4 w-4 text-muted-foreground" />
                          <span>{(recommendation.performance_prediction.estimated_accuracy * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="font-medium">예상 비용:</span>
                        <div className="flex items-center gap-2">
                          <DollarSign className="h-4 w-4 text-muted-foreground" />
                          <span>${recommendation.performance_prediction.estimated_cost.toFixed(3)}</span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="font-medium">신뢰도:</span>
                        <div className="flex items-center gap-2">
                          <Progress 
                            value={recommendation.performance_prediction.confidence_score * 100} 
                            className="w-16 h-2"
                          />
                          <span className={getConfidenceColor(recommendation.performance_prediction.confidence_score)}>
                            {(recommendation.performance_prediction.confidence_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-4 p-4 bg-muted rounded-lg">
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <Brain className="h-4 w-4" />
                      AI 추천 근거
                    </h4>
                    <p className="text-sm text-muted-foreground">{recommendation.reasoning}</p>
                  </div>
                </Card>
                
                {/* 대안 옵션 */}
                {recommendation.alternative_options.length > 0 && (
                  <Card className="p-6">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                      <Lightbulb className="h-5 w-5" />
                      대안 옵션
                    </h3>
                    
                    <div className="grid gap-4">
                      {recommendation.alternative_options.map((option, index) => (
                        <div key={index} className="p-4 border rounded-lg">
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="font-medium">{option.name}</h4>
                            <Badge variant="secondary">{option.model}</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mb-3">{option.description}</p>
                          
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div className="text-center">
                              <div className="font-medium">{option.estimated_time.toFixed(1)}초</div>
                              <div className="text-muted-foreground">처리 시간</div>
                            </div>
                            <div className="text-center">
                              <div className="font-medium">{(option.estimated_accuracy * 100).toFixed(1)}%</div>
                              <div className="text-muted-foreground">정확도</div>
                            </div>
                            <div className="text-center">
                              <div className="font-medium">{option.max_frames}개</div>
                              <div className="text-muted-foreground">프레임</div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}
                
                {/* 최적화 팁 */}
                {recommendation.optimization_tips.length > 0 && (
                  <Card className="p-6">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                      <Lightbulb className="h-5 w-5" />
                      최적화 팁
                    </h3>
                    
                    <ul className="space-y-2">
                      {recommendation.optimization_tips.map((tip, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{tip}</span>
                        </li>
                      ))}
                    </ul>
                  </Card>
                )}
                
                {/* 사용자 피드백 */}
                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Star className="h-5 w-5" />
                    이 추천이 도움이 되었나요?
                  </h3>
                  
                  <div className="flex gap-4">
                    <Button
                      variant={userFeedback === 'positive' ? 'default' : 'outline'}
                      onClick={() => handleFeedback('positive')}
                      className="gap-2"
                    >
                      <ThumbsUp className="h-4 w-4" />
                      도움됨
                    </Button>
                    <Button
                      variant={userFeedback === 'negative' ? 'destructive' : 'outline'}
                      onClick={() => handleFeedback('negative')}
                      className="gap-2"
                    >
                      <ThumbsDown className="h-4 w-4" />
                      개선 필요
                    </Button>
                  </div>
                  
                  {userFeedback && (
                    <Alert className="mt-4">
                      <Info className="h-4 w-4" />
                      <AlertDescription>
                        피드백이 기록되었습니다. 향후 최적화 개선에 활용하겠습니다.
                      </AlertDescription>
                    </Alert>
                  )}
                </Card>
              </div>
            ) : (
              <div className="text-center py-12">
                <Wand2 className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">최적화 결과가 없습니다</h3>
                <p className="text-muted-foreground mb-4">
                  프로필 탭에서 설정을 입력하고 AI 최적화를 실행해보세요.
                </p>
                <Button onClick={() => setActiveTab('profile')} variant="outline">
                  프로필 설정하기
                </Button>
              </div>
            )}
          </TabsContent>
          
          <TabsContent value="stats" className="space-y-4">
            <div className="text-center py-12">
              <BarChart3 className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">통계 기능 준비 중</h3>
              <p className="text-muted-foreground">
                최적화 사용 통계 및 성능 지표가 곧 제공될 예정입니다.
              </p>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}