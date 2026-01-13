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
  
  // 동적 클래스명 대신 조건부 클래스명 사용
  const iconBgClass = isAgentflow 
    ? 'bg-purple-100 dark:bg-purple-900' 
    : 'bg-blue-100 dark:bg-blue-900';
  const iconColorClass = isAgentflow 
    ? 'text-purple-600 dark:text-purple-400' 
    : 'text-blue-600 dark:text-blue-400';
  const buttonClass = isAgentflow 
    ? 'bg-purple-600 hover:bg-purple-700' 
    : 'bg-blue-600 hover:bg-blue-700';

  if (hasSearch) {
    return (
      <Card className="p-12">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
            <Icon className="h-6 w-6 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold mb-2">
            No search results for "{searchQuery}"
          </h3>
          <p className="text-muted-foreground mb-6">
            Try a different search term or create a new {isAgentflow ? 'Agentflow' : 'Chatflow'}
          </p>
          <div className="flex items-center justify-center gap-3">
            {onClearSearch && (
              <Button variant="outline" onClick={onClearSearch}>
                Clear Search
              </Button>
            )}
            <Button onClick={onNewFlow}>
              <Plus className="mr-2 h-4 w-4" />
              Create New
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  const suggestions = isAgentflow ? [
    {
      title: 'Research Agent Team',
      description: 'Multiple agents collaborate for information gathering',
      icon: '🔬',
      difficulty: 'Intermediate'
    },
    {
      title: 'Customer Support Team',
      description: 'Automate classification, response, and escalation',
      icon: '🎧',
      difficulty: 'Beginner'
    },
    {
      title: 'Content Generation Pipeline',
      description: 'Sequential processing from planning to publishing',
      icon: '✍️',
      difficulty: 'Advanced'
    }
  ] : [
    {
      title: 'RAG Chatbot',
      description: 'Document-based Q&A system',
      icon: '📚',
      difficulty: 'Beginner'
    },
    {
      title: 'Customer Support Bot',
      description: 'FAQ and ticket creation features',
      icon: '🎧',
      difficulty: 'Intermediate'
    },
    {
      title: 'Code Assistant',
      description: 'Code writing and review helper',
      icon: '💻',
      difficulty: 'Advanced'
    }
  ];

  return (
    <div className="space-y-8">
      {/* 메인 CTA */}
      <Card className="p-12 text-center bg-gradient-to-br from-gray-50 to-white dark:from-gray-900 dark:to-gray-800 border-2 border-dashed">
        <div className={`mx-auto h-16 w-16 rounded-full flex items-center justify-center mb-6 ${iconBgClass}`}>
          <Icon className={`h-8 w-8 ${iconColorClass}`} />
        </div>
        <h3 className="text-2xl font-bold mb-3">
          Create your first {isAgentflow ? 'Agentflow' : 'Chatflow'}
        </h3>
        <p className="text-muted-foreground mb-8 max-w-md mx-auto">
          {isAgentflow 
            ? 'Build systems where multiple AI agents collaborate to automate complex tasks'
            : 'Create RAG-based chatbots and AI assistants for natural conversations with users'
          }
        </p>
        <div className="flex items-center justify-center gap-4">
          <Button size="lg" onClick={onNewFlow} className={buttonClass}>
            <Plus className="mr-2 h-5 w-5" />
            Create from Scratch
          </Button>
          <Button size="lg" variant="outline" onClick={onShowTemplates}>
            <Sparkles className="mr-2 h-5 w-5" />
            Start with Template
          </Button>
        </div>
      </Card>

      {/* 추천 템플릿 */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="h-5 w-5 text-yellow-500" />
          <h4 className="text-lg font-semibold">Recommended Templates</h4>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {suggestions.map((suggestion, index) => (
            <Card key={index} className="cursor-pointer hover:shadow-lg transition-all border-2 hover:border-purple-400">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="text-2xl">{suggestion.icon}</div>
                  <Badge variant={
                    suggestion.difficulty === 'Beginner' ? 'default' :
                    suggestion.difficulty === 'Intermediate' ? 'secondary' : 'outline'
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
                  Get Started
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
            <h4 className="font-semibold mb-2">New to the platform?</h4>
            <p className="text-sm text-muted-foreground mb-3">
              Check out our {isAgentflow ? 'Agentflow' : 'Chatflow'} building guides and examples
            </p>
            <div className="flex gap-2">
              <Button size="sm" variant="outline">
                <BookOpen className="mr-2 h-3 w-3" />
                View Guide
              </Button>
              <Button size="sm" variant="outline">
                <Zap className="mr-2 h-3 w-3" />
                Browse Examples
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}