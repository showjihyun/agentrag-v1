'use client';

/**
 * Conversational Workflow Builder
 * 
 * Natural language interface for building workflows:
 * - Chat-based workflow creation
 * - Context-aware suggestions
 * - Multi-turn conversations
 * - Real-time workflow preview
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  Send,
  Sparkles,
  Bot,
  User,
  Loader2,
  Workflow,
  Play,
  Edit3,
  Copy,
  Check,
  ChevronRight,
  Lightbulb,
  Zap,
  Clock,
  ArrowRight,
  RefreshCw,
  ThumbsUp,
  ThumbsDown,
  Maximize2,
  Minimize2,
  X,
} from 'lucide-react';

// Types
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  workflow?: GeneratedWorkflow;
  suggestions?: string[];
  isLoading?: boolean;
  feedback?: 'positive' | 'negative';
}

export interface GeneratedWorkflow {
  id: string;
  name: string;
  description: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  estimatedTime?: string;
  complexity?: 'simple' | 'moderate' | 'complex';
}

export interface WorkflowNode {
  id: string;
  type: string;
  name: string;
  config?: Record<string, unknown>;
}

export interface WorkflowEdge {
  source: string;
  target: string;
}

interface ConversationalBuilderProps {
  onWorkflowGenerated: (workflow: GeneratedWorkflow) => void;
  onApplyWorkflow: (workflow: GeneratedWorkflow) => void;
  existingWorkflow?: GeneratedWorkflow;
  className?: string;
}

// Quick suggestion chips
const QUICK_SUGGESTIONS = [
  "매일 아침 뉴스 요약해서 Slack으로 보내줘",
  "GitHub PR이 생성되면 코드 리뷰 요청 알림",
  "고객 문의 이메일 자동 분류 및 응답",
  "웹사이트 변경 감지하고 알림 보내기",
  "데이터베이스 백업 자동화",
];

// Mini workflow preview
const WorkflowPreview: React.FC<{
  workflow: GeneratedWorkflow;
  onApply: () => void;
  onEdit: () => void;
}> = ({ workflow, onApply, onEdit }) => {
  return (
    <Card className="mt-3 border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h4 className="font-semibold flex items-center gap-2">
              <Workflow className="w-4 h-4 text-primary" />
              {workflow.name}
            </h4>
            <p className="text-sm text-muted-foreground mt-0.5">{workflow.description}</p>
          </div>
          <div className="flex items-center gap-1">
            {workflow.complexity && (
              <Badge variant="outline" className="text-xs">
                {workflow.complexity === 'simple' && '간단'}
                {workflow.complexity === 'moderate' && '보통'}
                {workflow.complexity === 'complex' && '복잡'}
              </Badge>
            )}
            {workflow.estimatedTime && (
              <Badge variant="outline" className="text-xs">
                <Clock className="w-3 h-3 mr-1" />
                {workflow.estimatedTime}
              </Badge>
            )}
          </div>
        </div>

        {/* Node flow visualization */}
        <div className="flex items-center gap-1 overflow-x-auto py-2 mb-3">
          {workflow.nodes.map((node, index) => (
            <React.Fragment key={node.id}>
              <div className="flex-shrink-0 px-3 py-1.5 bg-background border rounded-md text-xs font-medium">
                {node.name}
              </div>
              {index < workflow.nodes.length - 1 && (
                <ArrowRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
              )}
            </React.Fragment>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <Button size="sm" onClick={onApply} className="flex-1">
            <Play className="w-4 h-4 mr-1" />
            워크플로우 적용
          </Button>
          <Button size="sm" variant="outline" onClick={onEdit}>
            <Edit3 className="w-4 h-4 mr-1" />
            편집
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

// Message bubble component
const MessageBubble: React.FC<{
  message: Message;
  onApplyWorkflow?: (workflow: GeneratedWorkflow) => void;
  onEditWorkflow?: (workflow: GeneratedWorkflow) => void;
  onSuggestionClick?: (suggestion: string) => void;
  onFeedback?: (messageId: string, feedback: 'positive' | 'negative') => void;
}> = ({ message, onApplyWorkflow, onEditWorkflow, onSuggestionClick, onFeedback }) => {
  const isUser = message.role === 'user';

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      <Avatar className="w-8 h-8 flex-shrink-0">
        {isUser ? (
          <>
            <AvatarFallback className="bg-primary text-primary-foreground">
              <User className="w-4 h-4" />
            </AvatarFallback>
          </>
        ) : (
          <>
            <AvatarFallback className="bg-gradient-to-br from-purple-500 to-blue-500 text-white">
              <Bot className="w-4 h-4" />
            </AvatarFallback>
          </>
        )}
      </Avatar>

      <div className={cn('flex-1 max-w-[85%]', isUser && 'flex flex-col items-end')}>
        <div
          className={cn(
            'rounded-2xl px-4 py-2.5',
            isUser
              ? 'bg-primary text-primary-foreground rounded-tr-sm'
              : 'bg-muted rounded-tl-sm'
          )}
        >
          {message.isLoading ? (
            <div className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">생각하는 중...</span>
            </div>
          ) : (
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          )}
        </div>

        {/* Workflow preview */}
        {message.workflow && onApplyWorkflow && onEditWorkflow && (
          <WorkflowPreview
            workflow={message.workflow}
            onApply={() => onApplyWorkflow(message.workflow!)}
            onEdit={() => onEditWorkflow(message.workflow!)}
          />
        )}

        {/* Suggestions */}
        {message.suggestions && message.suggestions.length > 0 && onSuggestionClick && (
          <div className="flex flex-wrap gap-2 mt-2">
            {message.suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => onSuggestionClick(suggestion)}
                className="text-xs px-3 py-1.5 bg-background border rounded-full hover:bg-muted transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}

        {/* Feedback buttons for assistant messages */}
        {!isUser && !message.isLoading && onFeedback && (
          <div className="flex items-center gap-1 mt-2">
            <button
              onClick={() => onFeedback(message.id, 'positive')}
              className={cn(
                'p-1 rounded hover:bg-muted transition-colors',
                message.feedback === 'positive' && 'text-green-500'
              )}
            >
              <ThumbsUp className="w-3 h-3" />
            </button>
            <button
              onClick={() => onFeedback(message.id, 'negative')}
              className={cn(
                'p-1 rounded hover:bg-muted transition-colors',
                message.feedback === 'negative' && 'text-red-500'
              )}
            >
              <ThumbsDown className="w-3 h-3" />
            </button>
          </div>
        )}

        <span className="text-xs text-muted-foreground mt-1">
          {message.timestamp.toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
};

// Main component
export function ConversationalBuilder({
  onWorkflowGenerated,
  onApplyWorkflow,
  existingWorkflow,
  className,
}: ConversationalBuilderProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: '안녕하세요! 👋 어떤 워크플로우를 만들어 드릴까요?\n\n자연어로 원하는 자동화를 설명해주시면, 워크플로우를 생성해 드릴게요.',
      timestamp: new Date(),
      suggestions: QUICK_SUGGESTIONS.slice(0, 3),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Handle send message
  const handleSend = useCallback(async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // Add loading message
    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true,
    };
    setMessages(prev => [...prev, loadingMessage]);

    try {
      // Call API to generate workflow
      const response = await fetch('/api/agent-builder/workflow-nlp/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description: input.trim(),
          context: existingWorkflow ? { existing_workflow: existingWorkflow } : undefined,
        }),
      });

      const data = await response.json();

      // Remove loading message and add response
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== loadingMessage.id);
        
        const assistantMessage: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: data.success
            ? `워크플로우를 생성했습니다! "${data.workflow.name}"은(는) ${data.workflow.nodes?.length || 0}개의 노드로 구성되어 있습니다.`
            : '죄송합니다. 워크플로우 생성에 실패했습니다. 다시 시도해주세요.',
          timestamp: new Date(),
          workflow: data.success ? {
            id: data.workflow.id || Date.now().toString(),
            name: data.workflow.name,
            description: data.workflow.description,
            nodes: data.workflow.nodes || [],
            edges: data.workflow.edges || [],
            estimatedTime: data.estimated_time,
            complexity: data.complexity,
          } : undefined,
          suggestions: data.success
            ? ['노드 추가해줘', '조건 분기 넣어줘', '에러 처리 추가해줘']
            : ['다시 설명해줄게', '더 간단하게 만들어줘'],
        };

        return [...filtered, assistantMessage];
      });

      if (data.success && data.workflow) {
        onWorkflowGenerated({
          id: data.workflow.id || Date.now().toString(),
          name: data.workflow.name,
          description: data.workflow.description,
          nodes: data.workflow.nodes || [],
          edges: data.workflow.edges || [],
          estimatedTime: data.estimated_time,
          complexity: data.complexity,
        });
      }
    } catch (error) {
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== loadingMessage.id);
        return [
          ...filtered,
          {
            id: Date.now().toString(),
            role: 'assistant',
            content: '오류가 발생했습니다. 다시 시도해주세요.',
            timestamp: new Date(),
          },
        ];
      });
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, existingWorkflow, onWorkflowGenerated]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
    inputRef.current?.focus();
  };

  const handleFeedback = (messageId: string, feedback: 'positive' | 'negative') => {
    setMessages(prev =>
      prev.map(m =>
        m.id === messageId ? { ...m, feedback } : m
      )
    );
    // TODO: Send feedback to backend for learning
  };

  const handleApplyWorkflow = (workflow: GeneratedWorkflow) => {
    onApplyWorkflow(workflow);
    setMessages(prev => [
      ...prev,
      {
        id: Date.now().toString(),
        role: 'assistant',
        content: '워크플로우가 캔버스에 적용되었습니다! 🎉\n\n추가로 수정하고 싶은 부분이 있으면 말씀해주세요.',
        timestamp: new Date(),
        suggestions: ['트리거 변경해줘', '알림 추가해줘', '조건 수정해줘'],
      },
    ]);
  };

  const handleEditWorkflow = (workflow: GeneratedWorkflow) => {
    setMessages(prev => [
      ...prev,
      {
        id: Date.now().toString(),
        role: 'assistant',
        content: '어떤 부분을 수정하고 싶으신가요?',
        timestamp: new Date(),
        suggestions: ['노드 추가', '노드 삭제', '연결 변경', '설정 수정'],
      },
    ]);
  };

  return (
    <div
      className={cn(
        'flex flex-col bg-background border rounded-lg shadow-lg transition-all',
        isExpanded ? 'fixed inset-4 z-50' : 'h-[500px]',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b bg-gradient-to-r from-purple-500/10 to-blue-500/10">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-sm">AI 워크플로우 빌더</h3>
            <p className="text-xs text-muted-foreground">자연어로 워크플로우 생성</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea ref={scrollRef} className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map(message => (
            <MessageBubble
              key={message.id}
              message={message}
              onApplyWorkflow={handleApplyWorkflow}
              onEditWorkflow={handleEditWorkflow}
              onSuggestionClick={handleSuggestionClick}
              onFeedback={handleFeedback}
            />
          ))}
        </div>
      </ScrollArea>

      {/* Quick suggestions */}
      {messages.length === 1 && (
        <div className="px-4 pb-2">
          <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
            <Lightbulb className="w-3 h-3" />
            빠른 시작
          </p>
          <div className="flex flex-wrap gap-2">
            {QUICK_SUGGESTIONS.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="text-xs px-3 py-1.5 bg-muted rounded-full hover:bg-muted/80 transition-colors truncate max-w-[200px]"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-3 border-t">
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="원하는 워크플로우를 설명해주세요..."
              className="w-full px-4 py-2.5 pr-12 border rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary/50 min-h-[44px] max-h-[120px]"
              rows={1}
              disabled={isLoading}
            />
          </div>
          <Button
            size="icon"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="h-11 w-11 rounded-xl"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-2 text-center">
          Enter로 전송 • Shift+Enter로 줄바꿈
        </p>
      </div>
    </div>
  );
}

export default ConversationalBuilder;
