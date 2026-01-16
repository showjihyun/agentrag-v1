'use client';

/**
 * ThinkingBlock Component
 * 
 * AI의 추론 과정(Thinking/Reasoning)을 표시하는 컴포넌트
 * - 기본적으로 접힌 상태
 * - 클릭 시 펼쳐서 상세 추론 과정 표시
 * - 애니메이션 효과
 */

import React, { useState } from 'react';
import {
  Brain,
  ChevronDown,
  ChevronUp,
  Loader2,
  Sparkles,
  Lightbulb,
  Search,
  CheckCircle,
  Clock,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';

export interface ThinkingStep {
  id: string;
  type: 'analyzing' | 'searching' | 'reasoning' | 'planning' | 'synthesizing';
  content: string;
  timestamp: Date;
  status: 'pending' | 'in_progress' | 'completed';
}

interface ThinkingBlockProps {
  isThinking: boolean;
  currentStep?: string | null;
  steps?: ThinkingStep[];
  className?: string;
  defaultExpanded?: boolean;
}

const STEP_ICONS: Record<ThinkingStep['type'], React.ReactNode> = {
  analyzing: <Search className="h-3 w-3" />,
  searching: <Search className="h-3 w-3" />,
  reasoning: <Brain className="h-3 w-3" />,
  planning: <Lightbulb className="h-3 w-3" />,
  synthesizing: <Sparkles className="h-3 w-3" />,
};

const STEP_LABELS: Record<ThinkingStep['type'], string> = {
  analyzing: '분석 중',
  searching: '검색 중',
  reasoning: '추론 중',
  planning: '계획 수립',
  synthesizing: '종합 중',
};

export function ThinkingBlock({
  isThinking,
  currentStep,
  steps = [],
  className,
  defaultExpanded = false,
}: ThinkingBlockProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  if (!isThinking && steps.length === 0) {
    return null;
  }

  return (
    <Collapsible
      open={isExpanded}
      onOpenChange={setIsExpanded}
      className={cn("w-full", className)}
    >
      <div className="rounded-lg border bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950/20 dark:to-blue-950/20 overflow-hidden">
        {/* Header - 항상 표시 */}
        <CollapsibleTrigger asChild>
          <Button
            variant="ghost"
            className="w-full justify-between px-4 py-3 h-auto hover:bg-transparent"
          >
            <div className="flex items-center gap-2">
              {isThinking ? (
                <div className="relative">
                  <Brain className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                  <span className="absolute -top-1 -right-1 flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
                  </span>
                </div>
              ) : (
                <Brain className="h-5 w-5 text-muted-foreground" />
              )}
              
              <span className="font-medium text-sm">
                {isThinking ? 'Thinking...' : '추론 완료'}
              </span>
              
              {isThinking && currentStep && (
                <Badge variant="secondary" className="text-xs animate-pulse">
                  {currentStep}
                </Badge>
              )}
              
              {!isThinking && steps.length > 0 && (
                <Badge variant="outline" className="text-xs">
                  {steps.length}단계
                </Badge>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              {isThinking && (
                <Loader2 className="h-4 w-4 animate-spin text-purple-600" />
              )}
              {isExpanded ? (
                <ChevronUp className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
          </Button>
        </CollapsibleTrigger>

        {/* Content - 펼쳤을 때만 표시 */}
        <CollapsibleContent>
          <div className="px-4 pb-4 space-y-2">
            {/* 현재 진행 중인 단계 */}
            {isThinking && currentStep && (
              <div className="flex items-start gap-2 p-2 rounded bg-white/50 dark:bg-black/20">
                <Loader2 className="h-4 w-4 animate-spin text-purple-600 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-purple-700 dark:text-purple-300 italic">
                    {currentStep}
                  </p>
                </div>
              </div>
            )}
            
            {/* 완료된 단계들 */}
            {steps.length > 0 && (
              <div className="space-y-1.5">
                {steps.map((step, index) => (
                  <ThinkingStepItem 
                    key={step.id} 
                    step={step} 
                    index={index}
                    isLast={index === steps.length - 1}
                  />
                ))}
              </div>
            )}
            
            {/* 빈 상태 */}
            {!isThinking && steps.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-2">
                추론 과정이 기록되지 않았습니다
              </p>
            )}
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}

// 개별 단계 아이템
interface ThinkingStepItemProps {
  step: ThinkingStep;
  index: number;
  isLast: boolean;
}

function ThinkingStepItem({ step, index, isLast }: ThinkingStepItemProps) {
  const getStatusIcon = () => {
    switch (step.status) {
      case 'completed':
        return <CheckCircle className="h-3.5 w-3.5 text-green-500" />;
      case 'in_progress':
        return <Loader2 className="h-3.5 w-3.5 animate-spin text-purple-500" />;
      default:
        return <Clock className="h-3.5 w-3.5 text-muted-foreground" />;
    }
  };

  return (
    <div className="relative flex items-start gap-2">
      {/* 연결선 */}
      {!isLast && (
        <div className="absolute left-[7px] top-5 w-0.5 h-full bg-border" />
      )}
      
      {/* 상태 아이콘 */}
      <div className="relative z-10 mt-0.5">
        {getStatusIcon()}
      </div>
      
      {/* 내용 */}
      <div className="flex-1 min-w-0 pb-2">
        <div className="flex items-center gap-2 mb-0.5">
          <Badge 
            variant="outline" 
            className={cn(
              "text-xs gap-1",
              step.status === 'completed' && "border-green-200 bg-green-50 text-green-700 dark:border-green-800 dark:bg-green-950 dark:text-green-300"
            )}
          >
            {STEP_ICONS[step.type]}
            {STEP_LABELS[step.type]}
          </Badge>
          <span className="text-xs text-muted-foreground">
            {formatTime(step.timestamp)}
          </span>
        </div>
        <p className={cn(
          "text-sm",
          step.status === 'completed' 
            ? "text-foreground" 
            : "text-muted-foreground"
        )}>
          {step.content}
        </p>
      </div>
    </div>
  );
}

// 시간 포맷팅
function formatTime(date: Date): string {
  return date.toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

// 간단한 Thinking 인디케이터 (인라인용)
interface ThinkingIndicatorProps {
  isThinking: boolean;
  text?: string;
  className?: string;
}

export function ThinkingIndicator({
  isThinking,
  text = 'Thinking...',
  className,
}: ThinkingIndicatorProps) {
  if (!isThinking) return null;

  return (
    <div className={cn(
      "inline-flex items-center gap-2 text-sm text-purple-600 dark:text-purple-400",
      className
    )}>
      <Brain className="h-4 w-4" />
      <span className="italic">{text}</span>
      <span className="flex gap-0.5">
        <span className="w-1 h-1 rounded-full bg-purple-500 animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="w-1 h-1 rounded-full bg-purple-500 animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="w-1 h-1 rounded-full bg-purple-500 animate-bounce" style={{ animationDelay: '300ms' }} />
      </span>
    </div>
  );
}

export default ThinkingBlock;
