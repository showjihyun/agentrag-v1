'use client';

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import {
  Bot,
  MessageCircle,
  Send,
  Lightbulb,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Zap,
  Brain,
  Target,
  Users,
  Settings,
  BarChart3,
  Clock,
  Sparkles,
  ThumbsUp,
  ThumbsDown,
  Copy,
  RefreshCw,
} from 'lucide-react';

interface AIMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  suggestions?: AISuggestion[];
  actions?: AIAction[];
}

interface AISuggestion {
  id: string;
  title: string;
  description: string;
  type: 'optimization' | 'configuration' | 'troubleshooting' | 'insight';
  confidence: number;
  impact: 'low' | 'medium' | 'high';
  action?: () => void;
}

interface AIAction {
  id: string;
  label: string;
  description: string;
  icon: React.ComponentType<any>;
  onClick: () => void;
}

interface SupervisorAIAssistantProps {
  agentflowId: string;
  supervisorConfig: any;
  onConfigUpdate?: (config: any) => void;
}

export function SupervisorAIAssistant({
  agentflowId,
  supervisorConfig,
  onConfigUpdate,
}: SupervisorAIAssistantProps) {
  const { toast } = useToast();
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  // AI 어시스턴트 초기화
  useEffect(() => {
    const welcomeMessage: AIMessage = {
      id: 'welcome',
      type: 'assistant',
      content: `안녕하세요! 저는 슈퍼바이저 AI 어시스턴트입니다. 🤖

현재 Agentflow의 성능을 분석하고 최적화 방안을 제안해드릴 수 있습니다. 다음과 같은 도움을 받을 수 있어요:

• 성능 최적화 제안
• 설정 문제 진단 및 해결
• 에이전트 밸런싱 조언
• 실시간 모니터링 인사이트

무엇을 도와드릴까요?`,
      timestamp: new Date(),
      suggestions: [
        {
          id: 'performance-analysis',
          title: '성능 분석 실행',
          description: '현재 Agentflow의 성능을 종합적으로 분석합니다',
          type: 'insight',
          confidence: 0.95,
          impact: 'high',
        },
        {
          id: 'optimization-suggestions',
          title: '최적화 제안 받기',
          description: 'AI가 분석한 최적화 방안을 제안받습니다',
          type: 'optimization',
          confidence: 0.88,
          impact: 'high',
        },
        {
          id: 'troubleshoot',
          title: '문제 진단',
          description: '현재 발생 중인 문제를 자동으로 진단합니다',
          type: 'troubleshooting',
          confidence: 0.92,
          impact: 'medium',
        },
      ],
    };
    setMessages([welcomeMessage]);
  }, []);

  // AI 응답 생성
  const generateAIResponse = useMutation({
    mutationFn: (message: string) => agentBuilderAPI.getSupervisorAIResponse(agentflowId, message),
    onSuccess: (response) => {
      const aiMessage: AIMessage = {
        id: `ai-${Date.now()}`,
        type: 'assistant',
        content: response.content,
        timestamp: new Date(),
        suggestions: response.suggestions,
        actions: response.actions,
      };
      setMessages(prev => [...prev, aiMessage]);
      setIsTyping(false);
    },
    onError: () => {
      // Mock AI response for demo
      const mockResponse = generateMockAIResponse(inputMessage);
      const aiMessage: AIMessage = {
        id: `ai-${Date.now()}`,
        type: 'assistant',
        content: mockResponse.content,
        timestamp: new Date(),
        suggestions: mockResponse.suggestions,
        actions: mockResponse.actions,
      };
      setMessages(prev => [...prev, aiMessage]);
      setIsTyping(false);
    },
  });

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;

    const userMessage: AIMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);
    
    // AI 응답 생성
    setTimeout(() => {
      generateAIResponse.mutate(inputMessage);
    }, 1000);

    setInputMessage('');
  };

  const handleSuggestionClick = (suggestion: AISuggestion) => {
    const message = `${suggestion.title}에 대해 자세히 알려주세요.`;
    setInputMessage(message);
    handleSendMessage();
  };

  const generateMockAIResponse = (userMessage: string): { content: string; suggestions?: AISuggestion[]; actions?: AIAction[] } => {
    const lowerMessage = userMessage.toLowerCase();

    if (lowerMessage.includes('성능') || lowerMessage.includes('분석')) {
      return {
        content: `현재 Agentflow의 성능을 분석한 결과입니다:

📊 **성능 지표**
• 평균 응답시간: 2.3초 (목표: 3초 이하) ✅
• 성공률: 94.2% (목표: 90% 이상) ✅
• 처리량: 시간당 247건 (전주 대비 +15%) 📈

🎯 **주요 발견사항**
1. **데이터 분석가** 에이전트가 전체 작업의 65%를 처리하고 있어 병목 현상 발생
2. **보고서 작성자** 에이전트의 유휴 시간이 40%로 높음
3. 오전 9-11시 구간에 작업 집중으로 리소스 부족

💡 **개선 제안**
• 병렬 처리 활성화로 처리 속도 30% 향상 가능
• 작업 부하 재분배로 전체 효율성 25% 개선 예상`,
        suggestions: [
          {
            id: 'enable-parallel',
            title: '병렬 처리 활성화',
            description: '데이터 분석가 에이전트의 병렬 처리를 활성화합니다',
            type: 'optimization',
            confidence: 0.92,
            impact: 'high',
          },
          {
            id: 'rebalance-workload',
            title: '작업 부하 재분배',
            description: '에이전트 간 작업 부하를 균등하게 재분배합니다',
            type: 'optimization',
            confidence: 0.88,
            impact: 'medium',
          },
        ],
      };
    }

    if (lowerMessage.includes('최적화') || lowerMessage.includes('개선')) {
      return {
        content: `AI 분석을 통한 최적화 제안사항입니다:

🚀 **즉시 적용 가능한 최적화**

1. **에이전트 역할 재정의**
   • 현재: 데이터 분석가가 모든 분석 작업 담당
   • 제안: 전처리 전담 에이전트 추가로 작업 분산

2. **캐싱 전략 개선**
   • 반복적인 데이터 조회 작업 30% 감소 가능
   • 메모리 사용량 20% 절약 예상

3. **타임아웃 설정 최적화**
   • 현재 60초 → 45초로 조정 권장
   • 응답성 15% 향상 예상

⚡ **고급 최적화 (Phase 2)**
• 예측 기반 리소스 할당
• 동적 스케일링 활성화
• 머신러닝 기반 작업 우선순위 결정`,
        suggestions: [
          {
            id: 'apply-caching',
            title: '캐싱 전략 적용',
            description: '반복 작업에 대한 캐싱을 활성화합니다',
            type: 'optimization',
            confidence: 0.95,
            impact: 'high',
          },
          {
            id: 'adjust-timeouts',
            title: '타임아웃 최적화',
            description: '에이전트별 타임아웃을 최적값으로 조정합니다',
            type: 'configuration',
            confidence: 0.90,
            impact: 'medium',
          },
        ],
      };
    }

    if (lowerMessage.includes('문제') || lowerMessage.includes('오류') || lowerMessage.includes('진단')) {
      return {
        content: `시스템 진단을 완료했습니다:

🔍 **진단 결과**

✅ **정상 상태**
• 모든 에이전트 연결 상태 양호
• 메모리 사용량 정상 범위 (62%)
• 네트워크 지연 시간 정상

⚠️ **주의 필요**
• 보고서 작성자 에이전트 15분간 비활성 상태
• 오류율이 지난 주 대비 2% 증가 (5.8% → 7.8%)

🚨 **즉시 조치 필요**
• 없음

📋 **권장 조치사항**
1. 보고서 작성자 에이전트 상태 확인
2. 최근 오류 로그 분석
3. 예방적 재시작 스케줄링 고려`,
        suggestions: [
          {
            id: 'check-agent-status',
            title: '에이전트 상태 확인',
            description: '비활성 상태인 에이전트를 점검합니다',
            type: 'troubleshooting',
            confidence: 0.88,
            impact: 'medium',
          },
          {
            id: 'analyze-errors',
            title: '오류 로그 분석',
            description: '최근 발생한 오류들을 상세 분석합니다',
            type: 'troubleshooting',
            confidence: 0.92,
            impact: 'high',
          },
        ],
      };
    }

    return {
      content: `죄송합니다. 해당 질문에 대한 구체적인 답변을 준비 중입니다. 

다음과 같은 주제로 도움을 받을 수 있습니다:
• 성능 분석 및 최적화
• 설정 문제 진단
• 에이전트 관리 및 밸런싱
• 모니터링 및 알림 설정

구체적인 질문을 해주시면 더 정확한 답변을 드릴 수 있습니다! 😊`,
      suggestions: [
        {
          id: 'performance-help',
          title: '성능 관련 도움',
          description: '성능 최적화에 대한 구체적인 조언을 받습니다',
          type: 'insight',
          confidence: 0.85,
          impact: 'medium',
        },
      ],
    };
  };

  const getSuggestionIcon = (type: string) => {
    switch (type) {
      case 'optimization':
        return Zap;
      case 'configuration':
        return Settings;
      case 'troubleshooting':
        return AlertTriangle;
      case 'insight':
        return Lightbulb;
      default:
        return Brain;
    }
  };

  const getSuggestionColor = (type: string) => {
    switch (type) {
      case 'optimization':
        return 'border-green-200 bg-green-50 text-green-800';
      case 'configuration':
        return 'border-blue-200 bg-blue-50 text-blue-800';
      case 'troubleshooting':
        return 'border-red-200 bg-red-50 text-red-800';
      case 'insight':
        return 'border-purple-200 bg-purple-50 text-purple-800';
      default:
        return 'border-gray-200 bg-gray-50 text-gray-800';
    }
  };

  const getImpactBadge = (impact: string) => {
    switch (impact) {
      case 'high':
        return <Badge className="bg-red-500 hover:bg-red-600">높음</Badge>;
      case 'medium':
        return <Badge className="bg-yellow-500 hover:bg-yellow-600">중간</Badge>;
      case 'low':
        return <Badge className="bg-green-500 hover:bg-green-600">낮음</Badge>;
      default:
        return <Badge variant="outline">-</Badge>;
    }
  };

  return (
    <Card className="h-[600px] flex flex-col">
      <CardHeader className="border-b">
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-purple-600" />
          AI 어시스턴트
        </CardTitle>
        <CardDescription>
          슈퍼바이저 설정과 성능 최적화에 대한 AI 기반 조언을 받으세요
        </CardDescription>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        {/* 메시지 영역 */}
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {messages.map((message) => (
              <div key={message.id} className="space-y-3">
                <div className={`flex gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {message.type === 'assistant' && (
                    <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center">
                      <Bot className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                    </div>
                  )}
                  <div className={`max-w-[80%] rounded-lg p-3 ${
                    message.type === 'user' 
                      ? 'bg-purple-600 text-white' 
                      : 'bg-muted'
                  }`}>
                    <div className="whitespace-pre-wrap text-sm">{message.content}</div>
                    <div className="text-xs opacity-70 mt-1">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                  {message.type === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                      <MessageCircle className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    </div>
                  )}
                </div>

                {/* AI 제안사항 */}
                {message.suggestions && message.suggestions.length > 0 && (
                  <div className="ml-11 space-y-2">
                    <div className="text-sm font-medium text-muted-foreground">💡 제안사항</div>
                    {message.suggestions.map((suggestion) => {
                      const Icon = getSuggestionIcon(suggestion.type);
                      return (
                        <Card
                          key={suggestion.id}
                          className={`cursor-pointer transition-all hover:shadow-md ${getSuggestionColor(suggestion.type)}`}
                          onClick={() => handleSuggestionClick(suggestion)}
                        >
                          <CardContent className="p-3">
                            <div className="flex items-start justify-between">
                              <div className="flex items-start gap-2">
                                <Icon className="h-4 w-4 mt-0.5" />
                                <div className="flex-1">
                                  <div className="font-medium text-sm">{suggestion.title}</div>
                                  <div className="text-xs opacity-80 mt-1">{suggestion.description}</div>
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                {getImpactBadge(suggestion.impact)}
                                <Badge variant="outline" className="text-xs">
                                  {Math.round(suggestion.confidence * 100)}%
                                </Badge>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}

            {/* 타이핑 인디케이터 */}
            {isTyping && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                </div>
                <div className="bg-muted rounded-lg p-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* 입력 영역 */}
        <div className="border-t p-4">
          <div className="flex gap-2">
            <Input
              placeholder="AI 어시스턴트에게 질문하세요..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              className="flex-1"
            />
            <Button 
              onClick={handleSendMessage} 
              disabled={!inputMessage.trim() || isTyping}
              size="icon"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
          
          {/* 빠른 질문 버튼 */}
          <div className="flex flex-wrap gap-2 mt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setInputMessage('현재 성능을 분석해주세요');
                setTimeout(handleSendMessage, 100);
              }}
              className="text-xs"
            >
              성능 분석
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setInputMessage('최적화 방안을 제안해주세요');
                setTimeout(handleSendMessage, 100);
              }}
              className="text-xs"
            >
              최적화 제안
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setInputMessage('문제점을 진단해주세요');
                setTimeout(handleSendMessage, 100);
              }}
              className="text-xs"
            >
              문제 진단
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}