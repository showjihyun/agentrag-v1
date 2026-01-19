'use client';

import { useEffect, useState } from 'react';
import { Brain, Sparkles, Zap, Search, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ThinkingAnimationProps {
  stage?: 'analyzing' | 'reasoning' | 'searching' | 'generating' | 'complete';
  message?: string;
  className?: string;
}

const stages = [
  {
    id: 'analyzing',
    icon: Brain,
    label: 'Analyzing query',
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
  },
  {
    id: 'reasoning',
    icon: Sparkles,
    label: 'Reasoning',
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/10',
  },
  {
    id: 'searching',
    icon: Search,
    label: 'Searching knowledge',
    color: 'text-amber-500',
    bgColor: 'bg-amber-500/10',
  },
  {
    id: 'generating',
    icon: Zap,
    label: 'Generating response',
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
  },
  {
    id: 'complete',
    icon: CheckCircle2,
    label: 'Complete',
    color: 'text-emerald-500',
    bgColor: 'bg-emerald-500/10',
  },
];

export function ThinkingAnimation({ 
  stage = 'analyzing', 
  message,
  className 
}: ThinkingAnimationProps) {
  const [currentStageIndex, setCurrentStageIndex] = useState(0);
  const [dots, setDots] = useState('');

  // Auto-cycle through stages if no specific stage is provided
  useEffect(() => {
    if (stage === 'complete') return;

    const stageIndex = stages.findIndex(s => s.id === stage);
    if (stageIndex !== -1) {
      setCurrentStageIndex(stageIndex);
    } else {
      // Auto-cycle
      const interval = setInterval(() => {
        setCurrentStageIndex(prev => (prev + 1) % (stages.length - 1));
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [stage]);

  // Animated dots
  useEffect(() => {
    const interval = setInterval(() => {
      setDots(prev => (prev.length >= 3 ? '' : prev + '.'));
    }, 500);
    return () => clearInterval(interval);
  }, []);

  const currentStage = stages[currentStageIndex];
  const Icon = currentStage.icon;

  return (
    <div className={cn('flex items-start gap-3 p-4 rounded-lg', currentStage.bgColor, className)}>
      {/* Animated Icon */}
      <div className="relative">
        <div className={cn(
          'w-10 h-10 rounded-full flex items-center justify-center',
          currentStage.bgColor,
          'animate-pulse'
        )}>
          <Icon className={cn('h-5 w-5', currentStage.color)} />
        </div>
        {/* Ripple effect */}
        <div className={cn(
          'absolute inset-0 rounded-full animate-ping opacity-20',
          currentStage.bgColor
        )} />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className={cn('text-sm font-medium', currentStage.color)}>
            {currentStage.label}
          </span>
          <span className={cn('text-sm', currentStage.color)}>
            {dots}
          </span>
        </div>
        
        {message && (
          <p className="text-xs text-muted-foreground">
            {message}
          </p>
        )}

        {/* Progress bar */}
        <div className="mt-2 h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div 
            className={cn(
              'h-full transition-all duration-500 rounded-full',
              currentStage.color.replace('text-', 'bg-')
            )}
            style={{ 
              width: `${((currentStageIndex + 1) / stages.length) * 100}%` 
            }}
          />
        </div>

        {/* Stage indicators */}
        <div className="flex items-center gap-2 mt-2">
          {stages.slice(0, -1).map((s, index) => (
            <div
              key={s.id}
              className={cn(
                'w-2 h-2 rounded-full transition-all duration-300',
                index <= currentStageIndex
                  ? s.color.replace('text-', 'bg-')
                  : 'bg-gray-300 dark:bg-gray-600'
              )}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export function CompactThinkingAnimation({ className }: { className?: string }) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className="flex gap-1">
        <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: '0ms' }} />
        <div className="w-2 h-2 rounded-full bg-purple-500 animate-bounce" style={{ animationDelay: '150ms' }} />
        <div className="w-2 h-2 rounded-full bg-amber-500 animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
      <span className="text-xs text-muted-foreground">AI is thinking</span>
    </div>
  );
}
