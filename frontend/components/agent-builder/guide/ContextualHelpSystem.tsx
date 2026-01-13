/**
 * Contextual Help System
 * 상황별 맞춤 도움말 및 가이드 시스템
 */

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { 
  HelpCircle,
  Search,
  BookOpen,
  MessageSquare,
  Lightbulb,
  AlertTriangle,
  CheckCircle,
  ExternalLink,
  ChevronRight,
  ChevronDown,
  Star,
  ThumbsUp,
  ThumbsDown,
  X,
  Minimize2,
  Maximize2,
  RotateCcw,
  Send,
  Bot,
  User,
  Zap,
  Target,
  Settings,
  Code,
  Play,
  FileText,
  Video,
  Headphones
} from 'lucide-react';
import { OrchestrationTypeValue, ORCHESTRATION_TYPES } from '@/lib/constants/orchestration';

interface HelpArticle {
  id: string;
  title: string;
  content: string;
  category: 'getting-started' | 'patterns' | 'configuration' | 'troubleshooting' | 'best-practices';
  tags: string[];
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  estimatedReadTime: number; // in minutes
  lastUpdated: string;
  helpful: number;
  notHelpful: number;
  relatedArticles?: string[];
}

interface FAQ {
  id: string;
  question: string;
  answer: string;
  category: string;
  popularity: number;
  tags: string[];
}

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  helpful?: boolean;
}

interface ContextualHelpSystemProps {
  context?: {
    currentPage?: string;
    selectedPattern?: OrchestrationTypeValue;
    userAction?: string;
    errorMessage?: string;
  };
  isMinimized?: boolean;
  onToggleMinimize?: () => void;
  onClose?: () => void;
}

export const ContextualHelpSystem: React.FC<ContextualHelpSystemProps> = ({
  context,
  isMinimized = false,
  onToggleMinimize,
  onClose
}) => {
  const [activeTab, setActiveTab] = useState('help');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedFAQ, setExpandedFAQ] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Mock data
  const helpArticles: HelpArticle[] = [
    {
      id: 'consensus-getting-started',
      title: '합의 구축 패턴 시작하기',
      content: `
# 합의 구축 패턴 시작하기

합의 구축 패턴은 여러 Agent가 협력하여 최적의 결정을 내리는 강력한 방법입니다.

## 기본 설정

1. **투표 메커니즘 선택**
   - 단순 다수결: 빠른 결정이 필요한 경우
   - 가중 투표: Agent별 전문성을 반영하고 싶은 경우
   - 만장일치: 강한 합의가 필요한 중요한 결정

2. **합의 임계값 설정**
   - 일반적으로 60-80% 사이를 권장
   - 너무 높으면 합의 도달이 어려움
   - 너무 낮으면 약한 합의가 될 수 있음

3. **최대 라운드 수**
   - 무한 루프 방지를 위해 반드시 설정
   - 보통 3-7라운드가 적절

## 모범 사례

- Agent 역할을 명확히 정의하세요
- 토론 시간 제한을 설정하여 효율성을 높이세요
- 중재자 Agent를 활용하여 교착 상태를 방지하세요
      `,
      category: 'getting-started',
      tags: ['consensus', 'voting', 'configuration'],
      difficulty: 'beginner',
      estimatedReadTime: 5,
      lastUpdated: '2026-01-09',
      helpful: 24,
      notHelpful: 2
    },
    {
      id: 'swarm-optimization',
      title: '군집 지능 최적화 가이드',
      content: `
# 군집 지능 최적화 가이드

군집 지능 패턴의 성능을 최대화하는 방법을 알아보세요.

## 핵심 매개변수

### 관성 가중치 (Inertia Weight)
- 범위: 0.1 - 1.0
- 높은 값: 탐색 중심 (exploration)
- 낮은 값: 활용 중심 (exploitation)

### 인지/사회 가중치
- 인지 가중치: 개인 경험 반영도
- 사회 가중치: 집단 지식 반영도
- 균형이 중요 (보통 1.4 - 2.0)

## 성능 튜닝 팁

1. **초기 군집 크기**
   - 문제 복잡도에 따라 조정
   - 일반적으로 10-50개가 적절

2. **수렴 조건**
   - 너무 엄격하면 조기 종료
   - 너무 느슨하면 불필요한 계산

3. **적응형 매개변수**
   - 실행 중 동적 조정 고려
   - 성능 모니터링 기반 자동 튜닝
      `,
      category: 'best-practices',
      tags: ['swarm', 'optimization', 'performance'],
      difficulty: 'advanced',
      estimatedReadTime: 8,
      lastUpdated: '2026-01-08',
      helpful: 18,
      notHelpful: 1
    },
    {
      id: 'troubleshooting-timeouts',
      title: '타임아웃 문제 해결',
      content: `
# 타임아웃 문제 해결

오케스트레이션 실행 중 타임아웃이 발생하는 경우의 해결 방법입니다.

## 일반적인 원인

1. **Agent 응답 지연**
   - LLM 모델 응답 시간 확인
   - 네트워크 연결 상태 점검
   - 리소스 사용량 모니터링

2. **복잡한 작업**
   - 작업을 더 작은 단위로 분할
   - 병렬 처리 고려
   - 캐싱 활용

## 해결 방법

### 타임아웃 설정 조정
\`\`\`json
{
  "execution_timeout": 300000,  // 5분
  "agent_timeout": 60000,       // 1분
  "retry_attempts": 3
}
\`\`\`

### 성능 최적화
- 불필요한 Agent 제거
- 캐시 전략 개선
- 리소스 할당 최적화
      `,
      category: 'troubleshooting',
      tags: ['timeout', 'performance', 'debugging'],
      difficulty: 'intermediate',
      estimatedReadTime: 6,
      lastUpdated: '2026-01-07',
      helpful: 31,
      notHelpful: 4
    }
  ];

  const faqs: FAQ[] = [
    {
      id: 'faq-1',
      question: '어떤 오케스트레이션 패턴을 선택해야 하나요?',
      answer: '작업의 특성에 따라 선택하세요. 순차적 처리가 필요하면 Sequential, 독립적인 작업들은 Parallel, 복잡한 의사결정은 Consensus Building을 권장합니다.',
      category: 'patterns',
      popularity: 95,
      tags: ['pattern-selection', 'getting-started']
    },
    {
      id: 'faq-2',
      question: '합의 구축에서 합의가 이루어지지 않으면 어떻게 되나요?',
      answer: '최대 라운드 수에 도달하면 가장 높은 점수를 받은 선택지가 자동으로 선택되거나, 중재자 Agent가 최종 결정을 내립니다.',
      category: 'consensus',
      popularity: 87,
      tags: ['consensus', 'troubleshooting']
    },
    {
      id: 'faq-3',
      question: '군집 지능 패턴이 수렴하지 않는 이유는 무엇인가요?',
      answer: '수렴 임계값이 너무 엄격하거나, 매개변수 설정이 부적절할 수 있습니다. 관성 가중치와 학습률을 조정해보세요.',
      category: 'swarm',
      popularity: 73,
      tags: ['swarm', 'convergence', 'parameters']
    },
    {
      id: 'faq-4',
      question: 'Agent 수가 성능에 미치는 영향은?',
      answer: 'Agent 수가 많을수록 다양한 관점을 얻을 수 있지만, 통신 오버헤드와 합의 시간이 증가합니다. 보통 3-10개가 적절합니다.',
      category: 'performance',
      popularity: 68,
      tags: ['agents', 'performance', 'scaling']
    }
  ];

  // Filter articles based on search and context
  const filteredArticles = helpArticles.filter(article => {
    const matchesSearch = searchQuery === '' || 
      article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      article.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      article.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesContext = !context?.selectedPattern || 
      article.tags.includes(context.selectedPattern) ||
      article.content.toLowerCase().includes(context.selectedPattern);
    
    return matchesSearch && matchesContext;
  });

  // Get contextual suggestions
  const getContextualSuggestions = () => {
    const suggestions = [];
    
    if (context?.selectedPattern) {
      const patternInfo = ORCHESTRATION_TYPES[context.selectedPattern];
      suggestions.push({
        type: 'pattern-help',
        title: `${patternInfo?.name} 패턴 가이드`,
        description: `${patternInfo?.name} 패턴 사용법과 모범 사례를 확인하세요.`,
        action: () => setSearchQuery(context.selectedPattern)
      });
    }
    
    if (context?.errorMessage) {
      suggestions.push({
        type: 'error-help',
        title: '오류 해결 가이드',
        description: '현재 발생한 오류를 해결하는 방법을 찾아보세요.',
        action: () => setActiveTab('chat')
      });
    }
    
    if (context?.currentPage === 'configuration') {
      suggestions.push({
        type: 'config-help',
        title: '설정 도움말',
        description: '올바른 설정 방법과 권장 값을 확인하세요.',
        action: () => setSearchQuery('configuration')
      });
    }
    
    return suggestions;
  };

  // Simulate AI chat response
  const simulateAIResponse = async (userMessage: string) => {
    setIsTyping(true);
    
    // Simulate thinking time
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
    
    let response = '';
    
    // Context-aware responses
    if (userMessage.toLowerCase().includes('합의') || userMessage.toLowerCase().includes('consensus')) {
      response = `합의 구축 패턴에 대해 질문해주셨네요! 

합의 구축 패턴은 여러 Agent가 토론을 통해 최적의 결정을 내리는 방식입니다. 주요 설정 사항은:

1. **투표 메커니즘**: 단순 다수결, 가중 투표, 만장일치 중 선택
2. **합의 임계값**: 보통 60-80% 권장
3. **최대 라운드**: 3-7라운드가 적절

구체적으로 어떤 부분이 궁금하신가요?`;
    } else if (userMessage.toLowerCase().includes('군집') || userMessage.toLowerCase().includes('swarm')) {
      response = `군집 지능 패턴에 대한 질문이시군요!

군집 지능은 자연계의 집단 행동을 모방한 최적화 방법입니다:

🐜 **개미 군집 최적화 (ACO)**: 페로몬 트레일을 이용한 경로 탐색
🐦 **입자 군집 최적화 (PSO)**: 개체들의 협력적 탐색

핵심 매개변수:
- 관성 가중치: 0.7 (탐색/활용 균형)
- 인지/사회 가중치: 1.4 (개인/집단 경험 반영)

어떤 부분을 더 자세히 알고 싶으신가요?`;
    } else if (userMessage.toLowerCase().includes('오류') || userMessage.toLowerCase().includes('error')) {
      response = `오류 해결을 도와드리겠습니다! 

일반적인 오류 유형과 해결 방법:

🔴 **타임아웃 오류**
- 실행 시간 제한 늘리기
- Agent 수 줄이기
- 작업 단위 축소

🟡 **설정 오류**
- 필수 매개변수 확인
- 값 범위 검증
- 의존성 확인

🟢 **성능 문제**
- 리소스 사용량 모니터링
- 캐시 활용
- 병렬 처리 최적화

구체적인 오류 메시지를 알려주시면 더 정확한 해결책을 제공할 수 있습니다.`;
    } else {
      response = `안녕하세요! 오케스트레이션 패턴에 대해 도움을 드리겠습니다.

다음과 같은 주제로 질문해주세요:
- 패턴 선택 가이드
- 설정 방법
- 성능 최적화
- 오류 해결
- 모범 사례

구체적인 질문이 있으시면 언제든 말씀해주세요! 😊`;
    }
    
    setIsTyping(false);
    
    const aiMessage: ChatMessage = {
      id: `ai-${Date.now()}`,
      type: 'assistant',
      content: response,
      timestamp: new Date()
    };
    
    setChatMessages(prev => [...prev, aiMessage]);
  };

  const handleSendMessage = async () => {
    if (!chatInput.trim()) return;
    
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: chatInput,
      timestamp: new Date()
    };
    
    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    
    await simulateAIResponse(chatInput);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  if (isMinimized) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <Button
          onClick={onToggleMinimize}
          className="rounded-full w-12 h-12 shadow-lg"
        >
          <HelpCircle className="h-6 w-6" />
        </Button>
      </div>
    );
  }

  return (
    <Card className="fixed bottom-4 right-4 w-96 h-[600px] z-50 shadow-xl">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <HelpCircle className="h-5 w-5 text-blue-600" />
            <CardTitle className="text-lg">도움말</CardTitle>
          </div>
          
          <div className="flex items-center space-x-1">
            <Button variant="ghost" size="sm" onClick={onToggleMinimize}>
              <Minimize2 className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0 h-[calc(100%-80px)]">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
          <TabsList className="grid w-full grid-cols-3 mx-4">
            <TabsTrigger value="help">도움말</TabsTrigger>
            <TabsTrigger value="faq">FAQ</TabsTrigger>
            <TabsTrigger value="chat">AI 채팅</TabsTrigger>
          </TabsList>

          <TabsContent value="help" className="h-[calc(100%-50px)] overflow-hidden">
            <div className="p-4 space-y-4 h-full overflow-y-auto">
              {/* Contextual Suggestions */}
              {getContextualSuggestions().length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-semibold text-sm text-blue-600">추천 도움말</h4>
                  {getContextualSuggestions().map((suggestion, index) => (
                    <Alert key={index} className="cursor-pointer hover:bg-blue-50" onClick={suggestion.action}>
                      <Lightbulb className="h-4 w-4" />
                      <AlertDescription>
                        <div>
                          <p className="font-medium">{suggestion.title}</p>
                          <p className="text-sm text-gray-600">{suggestion.description}</p>
                        </div>
                      </AlertDescription>
                    </Alert>
                  ))}
                  <Separator />
                </div>
              )}

              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="도움말 검색..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* Articles */}
              <div className="space-y-3">
                {filteredArticles.map((article) => (
                  <Card key={article.id} className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardContent className="p-3">
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-medium text-sm">{article.title}</h4>
                        <Badge variant="outline" className="text-xs">
                          {article.difficulty === 'beginner' ? '초급' :
                           article.difficulty === 'intermediate' ? '중급' : '고급'}
                        </Badge>
                      </div>
                      
                      <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                        {article.content.substring(0, 100)}...
                      </p>
                      
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <div className="flex items-center space-x-2">
                          <span>{article.estimatedReadTime}분 읽기</span>
                          <span>•</span>
                          <div className="flex items-center space-x-1">
                            <ThumbsUp className="h-3 w-3" />
                            <span>{article.helpful}</span>
                          </div>
                        </div>
                        <ExternalLink className="h-3 w-3" />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="faq" className="h-[calc(100%-50px)] overflow-hidden">
            <div className="p-4 space-y-3 h-full overflow-y-auto">
              {faqs.map((faq) => (
                <Card key={faq.id} className="cursor-pointer">
                  <CardContent className="p-3">
                    <div 
                      className="flex items-center justify-between"
                      onClick={() => setExpandedFAQ(expandedFAQ === faq.id ? null : faq.id)}
                    >
                      <h4 className="font-medium text-sm">{faq.question}</h4>
                      {expandedFAQ === faq.id ? 
                        <ChevronDown className="h-4 w-4" /> : 
                        <ChevronRight className="h-4 w-4" />
                      }
                    </div>
                    
                    {expandedFAQ === faq.id && (
                      <div className="mt-3 pt-3 border-t">
                        <p className="text-sm text-gray-700">{faq.answer}</p>
                        <div className="flex items-center justify-between mt-3">
                          <div className="flex items-center space-x-2 text-xs text-gray-500">
                            <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                            <span>{faq.popularity}% 도움됨</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Button variant="ghost" size="sm">
                              <ThumbsUp className="h-3 w-3" />
                            </Button>
                            <Button variant="ghost" size="sm">
                              <ThumbsDown className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="chat" className="h-[calc(100%-50px)] overflow-hidden flex flex-col">
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {chatMessages.length === 0 && (
                <div className="text-center text-gray-500 mt-8">
                  <Bot className="h-12 w-12 mx-auto mb-2 text-blue-600" />
                  <p className="text-sm">AI 어시스턴트에게 질문해보세요!</p>
                  <p className="text-xs">오케스트레이션 패턴에 대해 도움을 드릴게요.</p>
                </div>
              )}
              
              {chatMessages.map((message) => (
                <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] p-3 rounded-lg ${
                    message.type === 'user' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    <div className="flex items-start space-x-2">
                      {message.type === 'assistant' && <Bot className="h-4 w-4 mt-0.5 flex-shrink-0" />}
                      <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                      {message.type === 'user' && <User className="h-4 w-4 mt-0.5 flex-shrink-0" />}
                    </div>
                    <div className="text-xs opacity-70 mt-1">
                      {message.timestamp.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                </div>
              ))}
              
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 p-3 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <Bot className="h-4 w-4" />
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={chatEndRef} />
            </div>
            
            <div className="p-4 border-t">
              <div className="flex space-x-2">
                <Input
                  placeholder="질문을 입력하세요..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="flex-1"
                />
                <Button onClick={handleSendMessage} disabled={!chatInput.trim()}>
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};