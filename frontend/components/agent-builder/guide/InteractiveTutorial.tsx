/**
 * Interactive Tutorial System
 * 오케스트레이션 패턴 학습을 위한 인터랙티브 튜토리얼
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { 
  Play,
  Pause,
  SkipForward,
  SkipBack,
  CheckCircle,
  Circle,
  BookOpen,
  Lightbulb,
  Target,
  Users,
  MessageSquare,
  Route,
  Hexagon,
  Bell,
  RefreshCw,
  ArrowRight,
  ArrowLeft,
  X,
  HelpCircle,
  Star,
  Clock,
  Award
} from 'lucide-react';
import { OrchestrationTypeValue, ORCHESTRATION_TYPES } from '@/lib/constants/orchestration';

interface TutorialStep {
  id: string;
  title: string;
  description: string;
  content: React.ReactNode;
  action?: {
    type: 'click' | 'input' | 'select' | 'wait';
    target?: string;
    value?: any;
    validation?: (value: any) => boolean;
  };
  tips?: string[];
  duration?: number; // in seconds
}

interface Tutorial {
  id: string;
  title: string;
  description: string;
  category: 'beginner' | 'intermediate' | 'advanced';
  estimatedTime: number; // in minutes
  patternType?: OrchestrationTypeValue;
  prerequisites?: string[];
  steps: TutorialStep[];
}

interface InteractiveTutorialProps {
  tutorialId?: string;
  onComplete?: (tutorialId: string, score: number) => void;
  onClose?: () => void;
}

export const InteractiveTutorial: React.FC<InteractiveTutorialProps> = ({
  tutorialId,
  onComplete,
  onClose
}) => {
  const [selectedTutorial, setSelectedTutorial] = useState<Tutorial | null>(null);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());
  const [isPlaying, setIsPlaying] = useState(false);
  const [userProgress, setUserProgress] = useState<Record<string, any>>({});
  const [startTime, setStartTime] = useState<Date | null>(null);

  // Tutorial definitions
  const tutorials: Tutorial[] = [
    {
      id: 'consensus_basics',
      title: '합의 구축 패턴 기초',
      description: '여러 Agent가 협력하여 최적의 결정을 내리는 방법을 학습합니다.',
      category: 'beginner',
      estimatedTime: 15,
      patternType: 'consensus_building',
      steps: [
        {
          id: 'intro',
          title: '합의 구축 패턴 소개',
          description: '합의 구축 패턴의 기본 개념과 사용 사례를 알아봅시다.',
          content: (
            <div className="space-y-4">
              <div className="flex items-center space-x-2 mb-4">
                <MessageSquare className="h-8 w-8 text-blue-600" />
                <h3 className="text-xl font-semibold">합의 구축 패턴</h3>
              </div>
              
              <p className="text-gray-700">
                합의 구축 패턴은 여러 Agent가 토론하고 협상하여 최적의 해결책에 대한 합의를 도출하는 방식입니다.
              </p>
              
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">주요 특징:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li>다양한 관점의 Agent들이 참여</li>
                  <li>투표 메커니즘을 통한 의사결정</li>
                  <li>라운드 기반 토론 진행</li>
                  <li>합의 임계값 설정 가능</li>
                </ul>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">적용 사례:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li>전략 수립 및 정책 결정</li>
                  <li>복잡한 문제 해결</li>
                  <li>품질 평가 및 검토</li>
                  <li>리스크 분석</li>
                </ul>
              </div>
            </div>
          ),
          duration: 120
        },
        {
          id: 'voting_mechanisms',
          title: '투표 메커니즘 이해',
          description: '다양한 투표 방식의 특징과 선택 기준을 학습합니다.',
          content: (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold mb-4">투표 메커니즘 종류</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border rounded-lg p-4">
                  <h4 className="font-semibold text-blue-600 mb-2">단순 다수결</h4>
                  <p className="text-sm text-gray-600 mb-2">가장 많은 표를 받은 선택지가 승리</p>
                  <div className="text-xs text-gray-500">
                    <p>✅ 빠른 결정</p>
                    <p>❌ 소수 의견 무시 가능</p>
                  </div>
                </div>
                
                <div className="border rounded-lg p-4">
                  <h4 className="font-semibold text-green-600 mb-2">가중 투표</h4>
                  <p className="text-sm text-gray-600 mb-2">Agent별 전문성에 따른 가중치 적용</p>
                  <div className="text-xs text-gray-500">
                    <p>✅ 전문성 반영</p>
                    <p>❌ 가중치 설정 복잡</p>
                  </div>
                </div>
                
                <div className="border rounded-lg p-4">
                  <h4 className="font-semibold text-purple-600 mb-2">만장일치</h4>
                  <p className="text-sm text-gray-600 mb-2">모든 Agent의 동의 필요</p>
                  <div className="text-xs text-gray-500">
                    <p>✅ 강한 합의</p>
                    <p>❌ 시간 소요 많음</p>
                  </div>
                </div>
                
                <div className="border rounded-lg p-4">
                  <h4 className="font-semibold text-orange-600 mb-2">절대 다수결</h4>
                  <p className="text-sm text-gray-600 mb-2">2/3 이상의 동의 필요</p>
                  <div className="text-xs text-gray-500">
                    <p>✅ 안정적 합의</p>
                    <p>❌ 높은 임계값</p>
                  </div>
                </div>
              </div>
            </div>
          ),
          duration: 180
        },
        {
          id: 'configuration_practice',
          title: '설정 실습',
          description: '합의 구축 패턴의 주요 설정을 직접 구성해봅시다.',
          content: (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold mb-4">설정 실습</h3>
              
              <Alert>
                <Lightbulb className="h-4 w-4" />
                <AlertDescription>
                  다음 시나리오에 맞는 설정을 선택해보세요: "5명의 전문가가 신제품 출시 전략을 결정"
                </AlertDescription>
              </Alert>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">투표 메커니즘</label>
                  <div className="grid grid-cols-2 gap-2">
                    {['majority', 'weighted', 'unanimous', 'supermajority'].map((mechanism) => (
                      <button
                        key={mechanism}
                        className={`p-2 border rounded text-sm ${
                          userProgress.voting_mechanism === mechanism 
                            ? 'bg-blue-100 border-blue-500' 
                            : 'hover:bg-gray-50'
                        }`}
                        onClick={() => setUserProgress(prev => ({ ...prev, voting_mechanism: mechanism }))}
                      >
                        {mechanism === 'majority' ? '단순 다수결' :
                         mechanism === 'weighted' ? '가중 투표' :
                         mechanism === 'unanimous' ? '만장일치' : '절대 다수결'}
                      </button>
                    ))}
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">
                    합의 임계값: {userProgress.consensus_threshold || 0.7}
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="1.0"
                    step="0.05"
                    value={userProgress.consensus_threshold || 0.7}
                    onChange={(e) => setUserProgress(prev => ({ 
                      ...prev, 
                      consensus_threshold: parseFloat(e.target.value) 
                    }))}
                    className="w-full"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">최대 라운드 수</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={userProgress.max_rounds || 5}
                    onChange={(e) => setUserProgress(prev => ({ 
                      ...prev, 
                      max_rounds: parseInt(e.target.value) 
                    }))}
                    className="w-full p-2 border rounded"
                  />
                </div>
              </div>
            </div>
          ),
          action: {
            type: 'select',
            validation: (progress) => 
              progress.voting_mechanism && 
              progress.consensus_threshold >= 0.5 && 
              progress.max_rounds > 0
          },
          duration: 300
        },
        {
          id: 'best_practices',
          title: '모범 사례',
          description: '합의 구축 패턴 사용 시 주의사항과 팁을 알아봅시다.',
          content: (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold mb-4">모범 사례 및 팁</h3>
              
              <div className="space-y-4">
                <div className="bg-green-50 border-l-4 border-green-500 p-4">
                  <h4 className="font-semibold text-green-800 mb-2">✅ 권장사항</h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-green-700">
                    <li>Agent 역할을 명확히 정의하세요</li>
                    <li>적절한 합의 임계값을 설정하세요 (보통 60-80%)</li>
                    <li>토론 시간 제한을 두어 효율성을 높이세요</li>
                    <li>중재자 Agent를 활용하여 교착 상태를 방지하세요</li>
                  </ul>
                </div>
                
                <div className="bg-red-50 border-l-4 border-red-500 p-4">
                  <h4 className="font-semibold text-red-800 mb-2">❌ 주의사항</h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-red-700">
                    <li>너무 많은 Agent는 의사결정을 지연시킵니다</li>
                    <li>100% 합의는 시간이 오래 걸릴 수 있습니다</li>
                    <li>가중치 설정 시 편향을 주의하세요</li>
                    <li>무한 루프를 방지하기 위해 최대 라운드를 설정하세요</li>
                  </ul>
                </div>
                
                <div className="bg-blue-50 border-l-4 border-blue-500 p-4">
                  <h4 className="font-semibold text-blue-800 mb-2">💡 성능 최적화</h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-blue-700">
                    <li>초기 투표로 명확한 선호도를 파악하세요</li>
                    <li>유사한 의견을 그룹화하여 효율성을 높이세요</li>
                    <li>이전 합의 결과를 학습 데이터로 활용하세요</li>
                    <li>실시간 모니터링으로 진행 상황을 추적하세요</li>
                  </ul>
                </div>
              </div>
            </div>
          ),
          duration: 240
        },
        {
          id: 'completion',
          title: '튜토리얼 완료',
          description: '합의 구축 패턴 학습을 완료했습니다!',
          content: (
            <div className="text-center space-y-4">
              <div className="flex justify-center">
                <Award className="h-16 w-16 text-yellow-500" />
              </div>
              
              <h3 className="text-2xl font-bold text-green-600">축하합니다! 🎉</h3>
              <p className="text-gray-600">합의 구축 패턴 튜토리얼을 성공적으로 완료했습니다.</p>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">학습 요약</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">완료 시간</p>
                    <p className="font-medium">
                      {startTime ? Math.round((Date.now() - startTime.getTime()) / 60000) : 0}분
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-600">완료율</p>
                    <p className="font-medium">100%</p>
                  </div>
                </div>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-semibold">다음 단계</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  <Button variant="outline" size="sm">
                    동적 라우팅 학습하기
                  </Button>
                  <Button variant="outline" size="sm">
                    실제 프로젝트 적용하기
                  </Button>
                </div>
              </div>
            </div>
          ),
          duration: 60
        }
      ]
    },
    {
      id: 'swarm_intelligence_intro',
      title: '군집 지능 패턴 입문',
      description: '자연의 군집 행동을 모방한 최적화 알고리즘을 학습합니다.',
      category: 'intermediate',
      estimatedTime: 20,
      patternType: 'swarm_intelligence',
      prerequisites: ['consensus_basics'],
      steps: [
        {
          id: 'swarm_intro',
          title: '군집 지능 개념',
          description: '자연계의 군집 행동과 AI에서의 응용을 알아봅시다.',
          content: (
            <div className="space-y-4">
              <div className="flex items-center space-x-2 mb-4">
                <Hexagon className="h-8 w-8 text-orange-600" />
                <h3 className="text-xl font-semibold">군집 지능 패턴</h3>
              </div>
              
              <p className="text-gray-700">
                군집 지능은 개미, 벌, 새 떼 등 자연계의 집단 행동을 모방하여 복잡한 문제를 해결하는 방법입니다.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-orange-50 p-4 rounded-lg">
                  <h4 className="font-semibold mb-2">🐜 개미 군집 최적화 (ACO)</h4>
                  <p className="text-sm text-gray-600">
                    개미가 페로몬을 이용해 최적 경로를 찾는 방식을 모방
                  </p>
                </div>
                
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-semibold mb-2">🐦 입자 군집 최적화 (PSO)</h4>
                  <p className="text-sm text-gray-600">
                    새 떼의 무리 행동을 모방한 최적화 알고리즘
                  </p>
                </div>
              </div>
            </div>
          ),
          duration: 150
        }
        // Additional steps would be added here
      ]
    }
  ];

  // Initialize tutorial
  useEffect(() => {
    if (tutorialId) {
      const tutorial = tutorials.find(t => t.id === tutorialId);
      if (tutorial) {
        setSelectedTutorial(tutorial);
        setStartTime(new Date());
      }
    }
  }, [tutorialId]);

  // Auto-advance for timed steps
  useEffect(() => {
    if (!isPlaying || !selectedTutorial) return;

    const currentStep = selectedTutorial.steps[currentStepIndex];
    if (currentStep?.duration && !currentStep.action) {
      const timer = setTimeout(() => {
        nextStep();
      }, currentStep.duration * 1000);

      return () => clearTimeout(timer);
    }
  }, [currentStepIndex, isPlaying, selectedTutorial]);

  const nextStep = useCallback(() => {
    if (!selectedTutorial) return;

    if (currentStepIndex < selectedTutorial.steps.length - 1) {
      setCurrentStepIndex(prev => prev + 1);
      setCompletedSteps(prev => new Set([...prev, selectedTutorial.steps[currentStepIndex].id]));
    } else {
      // Tutorial completed
      const score = calculateScore();
      onComplete?.(selectedTutorial.id, score);
    }
  }, [currentStepIndex, selectedTutorial, onComplete]);

  const prevStep = useCallback(() => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(prev => prev - 1);
    }
  }, [currentStepIndex]);

  const calculateScore = () => {
    if (!selectedTutorial) return 0;
    
    const completionRate = completedSteps.size / selectedTutorial.steps.length;
    const timeBonus = startTime ? Math.max(0, 1 - (Date.now() - startTime.getTime()) / (selectedTutorial.estimatedTime * 60000)) : 0;
    
    return Math.round((completionRate * 70 + timeBonus * 30) * 100) / 100;
  };

  const validateCurrentStep = () => {
    if (!selectedTutorial) return false;
    
    const currentStep = selectedTutorial.steps[currentStepIndex];
    if (currentStep.action?.validation) {
      return currentStep.action.validation(userProgress);
    }
    
    return true;
  };

  if (!selectedTutorial) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center">
            <BookOpen className="h-6 w-6 mr-2" />
            인터랙티브 튜토리얼
          </CardTitle>
          <CardDescription>오케스트레이션 패턴을 단계별로 학습해보세요</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {tutorials.map((tutorial) => (
              <Card key={tutorial.id} className="cursor-pointer hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <Badge className={
                      tutorial.category === 'beginner' ? 'bg-green-100 text-green-800' :
                      tutorial.category === 'intermediate' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }>
                      {tutorial.category === 'beginner' ? '초급' :
                       tutorial.category === 'intermediate' ? '중급' : '고급'}
                    </Badge>
                    <div className="flex items-center text-sm text-gray-500">
                      <Clock className="h-4 w-4 mr-1" />
                      {tutorial.estimatedTime}분
                    </div>
                  </div>
                  
                  <h3 className="font-semibold text-lg mb-2">{tutorial.title}</h3>
                  <p className="text-gray-600 text-sm mb-3">{tutorial.description}</p>
                  
                  {tutorial.prerequisites && (
                    <div className="mb-3">
                      <p className="text-xs text-gray-500 mb-1">선수 과정:</p>
                      <div className="flex flex-wrap gap-1">
                        {tutorial.prerequisites.map((prereq) => (
                          <Badge key={prereq} variant="outline" className="text-xs">
                            {prereq}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <Button 
                    className="w-full"
                    onClick={() => {
                      setSelectedTutorial(tutorial);
                      setStartTime(new Date());
                    }}
                  >
                    <Play className="h-4 w-4 mr-2" />
                    시작하기
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const currentStep = selectedTutorial.steps[currentStepIndex];
  const progress = ((currentStepIndex + 1) / selectedTutorial.steps.length) * 100;

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center">
              <BookOpen className="h-6 w-6 mr-2" />
              {selectedTutorial.title}
            </CardTitle>
            <CardDescription>
              단계 {currentStepIndex + 1} / {selectedTutorial.steps.length}: {currentStep.title}
            </CardDescription>
          </div>
          
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-gray-600">
            <span>진행률</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="w-full" />
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Step Content */}
        <div className="min-h-[400px]">
          <h3 className="text-xl font-semibold mb-4">{currentStep.title}</h3>
          <p className="text-gray-600 mb-6">{currentStep.description}</p>
          
          {currentStep.content}
          
          {currentStep.tips && (
            <div className="mt-6 bg-blue-50 p-4 rounded-lg">
              <h4 className="font-semibold text-blue-800 mb-2 flex items-center">
                <Lightbulb className="h-4 w-4 mr-1" />
                팁
              </h4>
              <ul className="list-disc list-inside space-y-1 text-sm text-blue-700">
                {currentStep.tips.map((tip, index) => (
                  <li key={index}>{tip}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between pt-4 border-t">
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={prevStep}
              disabled={currentStepIndex === 0}
            >
              <ArrowLeft className="h-4 w-4 mr-1" />
              이전
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsPlaying(!isPlaying)}
            >
              {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            </Button>
          </div>
          
          <div className="flex items-center space-x-2">
            {currentStep.action ? (
              <Button
                onClick={nextStep}
                disabled={!validateCurrentStep()}
              >
                {currentStepIndex === selectedTutorial.steps.length - 1 ? '완료' : '다음'}
                <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            ) : (
              <Button
                variant="outline"
                onClick={nextStep}
              >
                {currentStepIndex === selectedTutorial.steps.length - 1 ? '완료' : '다음'}
                <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};