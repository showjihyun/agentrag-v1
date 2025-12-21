'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Plus, 
  Users, 
  MessageSquare, 
  Sparkles,
  ArrowRight,
  BookOpen,
  Zap
} from 'lucide-react';

interface SmartEmptyStateProps {
  type: 'agentflow' | 'chatflow';
  hasSearch: boolean;
  searchQuery?: string;
  onNewFlow: () => void;
  onShowTemplates: () => void;
  onClearSearch?: () => void;
}

export function SmartEmptyState({ 
  type, 
  hasSearch, 
  searchQuery, 
  onNewFlow, 
  onShowTemplates,
  onClearSearch 
}: SmartEmptyStateProps) {
  const isAgentflow = type === 'agentflow';
  const Icon = isAgentflow ? Users : MessageSquare;
  const primaryColor = isAgentflow ? 'purple' : 'blue';

  if (hasSearch) {
    return (
      <Card className="p-12">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
            <Icon className="h-6 w-6 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold mb-2">
            "{searchQuery}"에 대한 검색 결과가 없습니다
          </h3>
          <p className="text-muted-foreground mb-6">
            다른 검색어를 시도하거나 새로운 {isAgentflow ? 'Agentflow' : 'Chatflow'}를 만들어보세요
          </p>
          <div className="flex items-center justify-center gap-3">
            {onClearSearch && (
              <Button variant="outline" onClick={onClearSearch}>
                검색 초기화
              </Button>
            )}
            <Button onClick={onNewFlow}>
              <Plus className="mr-2 h-4 w-4" />
              새로 만들기
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  const suggestions = isAgentflow ? [
    {
      title: '리서치 에이전트 팀',
      description: '여러 에이전트가 협력하여 정보 수집',
      icon: '🔬',
      difficulty: '중급'
    },
    {
      title: '고객 지원 팀',
      description: '분류, 응답, 에스컬레이션 자동화',
      icon: '🎧',
      difficulty: '초급'
    },
    {
      title: '콘텐츠 생성 파이프라인',
      description: '기획부터 발행까지 순차 처리',
      icon: '✍️',
      difficulty: '고급'
    }
  ] : [
    {
      title: 'RAG 챗봇',
      description: '문서 기반 질의응답 시스템',
      icon: '📚',
      difficulty: '초급'
    },
    {
      title: '고객 지원 봇',
      description: 'FAQ 및 티켓 생성 기능',
      icon: '🎧',
      difficulty: '중급'
    },
    {
      title: '코드 어시스턴트',
      description: '코드 작성 및 리뷰 도우미',
      icon: '💻',
      difficulty: '고급'
    }
  ];

  return (
    <div className="space-y-8">
      {/* 메인 CTA */}
      <Card className="p-12 text-center bg-gradient-to-br from-gray-50 to-white dark:from-gray-900 dark:to-gray-800 border-2 border-dashed">
        <div className={`mx-auto h-16 w-16 rounded-full bg-${primaryColor}-100 dark:bg-${primaryColor}-900 flex items-center justify-center mb-6`}>
          <Icon className={`h-8 w-8 text-${primaryColor}-600 dark:text-${primaryColor}-400`} />
        </div>
        <h3 className="text-2xl font-bold mb-3">
          첫 번째 {isAgentflow ? 'Agentflow' : 'Chatflow'}를 만들어보세요
        </h3>
        <p className="text-muted-foreground mb-8 max-w-md mx-auto">
          {isAgentflow 
            ? '여러 AI 에이전트가 협력하여 복잡한 작업을 자동화하는 시스템을 구축하세요'
            : 'RAG 기반 챗봇과 AI 어시스턴트로 사용자와 자연스럽게 대화하세요'
          }
        </p>
        <div className="flex items-center justify-center gap-4">
          <Button size="lg" onClick={onNewFlow} className={`bg-${primaryColor}-600 hover:bg-${primaryColor}-700`}>
            <Plus className="mr-2 h-5 w-5" />
            직접 만들기
          </Button>
          <Button size="lg" variant="outline" onClick={onShowTemplates}>
            <Sparkles className="mr-2 h-5 w-5" />
            템플릿으로 시작
          </Button>
        </div>
      </Card>

      {/* 추천 템플릿 */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="h-5 w-5 text-yellow-500" />
          <h4 className="text-lg font-semibold">추천 템플릿</h4>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {suggestions.map((suggestion, index) => (
            <Card key={index} className="cursor-pointer hover:shadow-lg transition-all border-2 hover:border-purple-400">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="text-2xl">{suggestion.icon}</div>
                  <Badge variant={
                    suggestion.difficulty === '초급' ? 'default' :
                    suggestion.difficulty === '중급' ? 'secondary' : 'outline'
                  } className="text-xs">
                    {suggestion.difficulty}
                  </Badge>
                </div>
                <CardTitle className="text-base">{suggestion.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-3">
                  {suggestion.description}
                </p>
                <Button size="sm" variant="ghost" className="w-full justify-between">
                  시작하기
                  <ArrowRight className="h-3 w-3" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* 학습 리소스 */}
      <Card className="p-6 bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-4">
          <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
            <BookOpen className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="flex-1">
            <h4 className="font-semibold mb-2">처음 사용하시나요?</h4>
            <p className="text-sm text-muted-foreground mb-3">
              {isAgentflow ? 'Agentflow' : 'Chatflow'} 구축 가이드와 예제를 확인해보세요
            </p>
            <div className="flex gap-2">
              <Button size="sm" variant="outline">
                <BookOpen className="mr-2 h-3 w-3" />
                가이드 보기
              </Button>
              <Button size="sm" variant="outline">
                <Zap className="mr-2 h-3 w-3" />
                예제 둘러보기
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}