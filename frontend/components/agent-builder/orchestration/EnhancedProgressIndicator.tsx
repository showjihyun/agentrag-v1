/**
 * Enhanced Progress Indicator
 * 향상된 진행률 표시기
 */

import React from 'react';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, AlertCircle, Clock, Target } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Step {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<any>;
  estimatedTime?: string;
  difficulty?: 'easy' | 'medium' | 'hard';
}

interface EnhancedProgressIndicatorProps {
  steps: Step[];
  currentStep: number;
  completedSteps: number[];
  invalidSteps: number[];
  className?: string;
  showEstimatedTime?: boolean;
  showDifficulty?: boolean;
  onStepClick?: (stepIndex: number) => void;
}

export function EnhancedProgressIndicator({
  steps,
  currentStep,
  completedSteps,
  invalidSteps,
  className,
  showEstimatedTime = true,
  showDifficulty = true,
  onStepClick
}: EnhancedProgressIndicatorProps) {
  const progress = ((currentStep + 1) / steps.length) * 100;
  const totalEstimatedTime = steps.reduce((total, step) => {
    if (step.estimatedTime) {
      const minutes = parseInt(step.estimatedTime.replace(/\D/g, ''));
      return total + (minutes || 0);
    }
    return total;
  }, 0);

  const getDifficultyColor = (difficulty?: string) => {
    switch (difficulty) {
      case 'easy': return 'bg-green-100 text-green-700';
      case 'medium': return 'bg-yellow-100 text-yellow-700';
      case 'hard': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getDifficultyIcon = (difficulty?: string) => {
    switch (difficulty) {
      case 'easy': return '●';
      case 'medium': return '●●';
      case 'hard': return '●●●';
      default: return '●';
    }
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* 전체 진행률 */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium">전체 진행률</span>
          <span className="text-gray-600">{currentStep + 1} / {steps.length}</span>
        </div>
        <Progress value={progress} className="h-3" />
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>{Math.round(progress)}% 완료</span>
          {showEstimatedTime && totalEstimatedTime > 0 && (
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              예상 {totalEstimatedTime}분
            </span>
          )}
        </div>
      </div>

      {/* 단계별 상세 진행률 */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-gray-700">단계별 진행 상황</h4>
        <div className="space-y-2">
          {steps.map((step, index) => {
            const StepIcon = step.icon;
            const isCompleted = completedSteps.includes(index);
            const isCurrent = index === currentStep;
            const isInvalid = invalidSteps.includes(index);
            const isAccessible = index <= currentStep || isCompleted;

            return (
              <div
                key={step.id}
                className={cn(
                  'flex items-center gap-3 p-3 rounded-lg transition-all duration-200',
                  'border border-transparent',
                  isCurrent && 'bg-blue-50 border-blue-200 shadow-sm',
                  isCompleted && 'bg-green-50 border-green-200',
                  isInvalid && 'bg-red-50 border-red-200',
                  !isCurrent && !isCompleted && !isInvalid && 'bg-gray-50',
                  isAccessible && onStepClick && 'cursor-pointer hover:shadow-md',
                  !isAccessible && 'opacity-60'
                )}
                onClick={() => isAccessible && onStepClick?.(index)}
              >
                {/* 아이콘 */}
                <div className={cn(
                  'flex-shrink-0 p-2 rounded-full transition-colors',
                  isCurrent && 'bg-blue-500 text-white',
                  isCompleted && 'bg-green-500 text-white',
                  isInvalid && 'bg-red-500 text-white',
                  !isCurrent && !isCompleted && !isInvalid && 'bg-gray-300 text-gray-600'
                )}>
                  {isCompleted ? (
                    <CheckCircle2 className="w-4 h-4" />
                  ) : isInvalid ? (
                    <AlertCircle className="w-4 h-4" />
                  ) : (
                    <StepIcon className="w-4 h-4" />
                  )}
                </div>

                {/* 내용 */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h5 className={cn(
                      'text-sm font-medium truncate',
                      isCurrent && 'text-blue-900',
                      isCompleted && 'text-green-900',
                      isInvalid && 'text-red-900',
                      !isCurrent && !isCompleted && !isInvalid && 'text-gray-700'
                    )}>
                      {step.title}
                    </h5>
                    
                    {/* 상태 배지 */}
                    {isCurrent && (
                      <Badge variant="secondary" className="text-xs bg-blue-100 text-blue-700">
                        진행 중
                      </Badge>
                    )}
                    {isCompleted && (
                      <Badge variant="secondary" className="text-xs bg-green-100 text-green-700">
                        완료
                      </Badge>
                    )}
                    {isInvalid && (
                      <Badge variant="secondary" className="text-xs bg-red-100 text-red-700">
                        오류
                      </Badge>
                    )}
                  </div>
                  
                  <p className={cn(
                    'text-xs text-gray-600 mb-2',
                    isCurrent && 'text-blue-700',
                    isCompleted && 'text-green-700',
                    isInvalid && 'text-red-700'
                  )}>
                    {step.description}
                  </p>

                  {/* 메타 정보 */}
                  <div className="flex items-center gap-3 text-xs">
                    {showEstimatedTime && step.estimatedTime && (
                      <span className="flex items-center gap-1 text-gray-500">
                        <Clock className="w-3 h-3" />
                        {step.estimatedTime}
                      </span>
                    )}
                    
                    {showDifficulty && step.difficulty && (
                      <span className={cn(
                        'flex items-center gap-1 px-2 py-1 rounded-full text-xs',
                        getDifficultyColor(step.difficulty)
                      )}>
                        <Target className="w-3 h-3" />
                        {getDifficultyIcon(step.difficulty)} {step.difficulty}
                      </span>
                    )}
                  </div>
                </div>

                {/* 단계 번호 */}
                <div className={cn(
                  'flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium',
                  isCurrent && 'bg-blue-500 text-white',
                  isCompleted && 'bg-green-500 text-white',
                  isInvalid && 'bg-red-500 text-white',
                  !isCurrent && !isCompleted && !isInvalid && 'bg-gray-300 text-gray-600'
                )}>
                  {index + 1}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 요약 통계 */}
      <div className="grid grid-cols-3 gap-3 pt-3 border-t">
        <div className="text-center">
          <div className="text-lg font-semibold text-green-600">{completedSteps.length}</div>
          <div className="text-xs text-gray-600">완료</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-blue-600">
            {currentStep < steps.length ? 1 : 0}
          </div>
          <div className="text-xs text-gray-600">진행 중</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-red-600">{invalidSteps.length}</div>
          <div className="text-xs text-gray-600">오류</div>
        </div>
      </div>
    </div>
  );
}

/**
 * 간단한 진행률 표시기
 */
export function SimpleProgressIndicator({
  current,
  total,
  className
}: {
  current: number;
  total: number;
  className?: string;
}) {
  const progress = (current / total) * 100;

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium">진행률</span>
        <span className="text-gray-600">{current} / {total}</span>
      </div>
      <Progress value={progress} className="h-2" />
      <div className="text-xs text-gray-500 text-right">
        {Math.round(progress)}% 완료
      </div>
    </div>
  );
}

/**
 * 원형 진행률 표시기
 */
export function CircularProgressIndicator({
  current,
  total,
  size = 60,
  strokeWidth = 4,
  className
}: {
  current: number;
  total: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
}) {
  const progress = (current / total) * 100;
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)}>
      <svg
        width={size}
        height={size}
        className="transform -rotate-90"
      >
        {/* 배경 원 */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          className="text-gray-200"
        />
        {/* 진행률 원 */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="text-blue-500 transition-all duration-300 ease-in-out"
        />
      </svg>
      
      {/* 중앙 텍스트 */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-sm font-semibold text-gray-900">
          {Math.round(progress)}%
        </span>
        <span className="text-xs text-gray-500">
          {current}/{total}
        </span>
      </div>
    </div>
  );
}