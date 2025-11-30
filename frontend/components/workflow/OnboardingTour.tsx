'use client';

/**
 * Onboarding Tour Component
 * 
 * Interactive tutorial for first-time users with:
 * - Step-by-step guidance
 * - Highlight animations
 * - Progress tracking
 * - Skip/Complete options
 */

import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  X,
  ChevronRight,
  ChevronLeft,
  Sparkles,
  MousePointer2,
  Workflow,
  Play,
  Settings,
  Zap,
  CheckCircle2,
} from 'lucide-react';

interface TourStep {
  id: string;
  title: string;
  description: string;
  target?: string; // CSS selector for element to highlight
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
  icon?: React.ReactNode;
  action?: string; // Action hint for user
}

const TOUR_STEPS: TourStep[] = [
  {
    id: 'welcome',
    title: '워크플로우 에디터에 오신 것을 환영합니다! 👋',
    description: '이 가이드를 통해 워크플로우를 만드는 방법을 알아보세요. 드래그 앤 드롭으로 쉽게 자동화를 구축할 수 있습니다.',
    position: 'center',
    icon: <Sparkles className="h-6 w-6" />,
  },
  {
    id: 'palette',
    title: '블록 팔레트',
    description: '왼쪽 패널에서 다양한 블록과 도구를 찾을 수 있습니다. 검색하거나 카테고리별로 탐색하세요.',
    target: '[data-tour="block-palette"]',
    position: 'right',
    icon: <Workflow className="h-5 w-5" />,
    action: '블록을 클릭하거나 드래그하여 캔버스에 추가하세요',
  },
  {
    id: 'canvas',
    title: '워크플로우 캔버스',
    description: '이곳에서 노드를 배치하고 연결합니다. 마우스로 드래그하여 이동하고, 스크롤로 확대/축소하세요.',
    target: '[data-tour="workflow-canvas"]',
    position: 'bottom',
    icon: <MousePointer2 className="h-5 w-5" />,
    action: '노드 사이를 드래그하여 연결하세요',
  },
  {
    id: 'node-config',
    title: '노드 설정',
    description: '노드를 클릭하면 오른쪽에 설정 패널이 나타납니다. 각 노드의 동작을 세부적으로 구성할 수 있습니다.',
    target: '[data-tour="properties-panel"]',
    position: 'left',
    icon: <Settings className="h-5 w-5" />,
    action: '노드를 선택하고 속성을 편집하세요',
  },
  {
    id: 'execution',
    title: '워크플로우 실행',
    description: '상단의 실행 버튼으로 워크플로우를 테스트하세요. 실시간으로 각 노드의 실행 상태를 확인할 수 있습니다.',
    target: '[data-tour="execution-controls"]',
    position: 'bottom',
    icon: <Play className="h-5 w-5" />,
    action: '실행 버튼을 클릭하여 워크플로우를 시작하세요',
  },
  {
    id: 'complete',
    title: '준비 완료! 🎉',
    description: '이제 첫 번째 워크플로우를 만들 준비가 되었습니다. 트리거 노드로 시작하여 원하는 자동화를 구축해보세요!',
    position: 'center',
    icon: <CheckCircle2 className="h-6 w-6 text-green-500" />,
  },
];

interface OnboardingTourProps {
  onComplete?: () => void;
  onSkip?: () => void;
  forceShow?: boolean;
}

const STORAGE_KEY = 'workflow_onboarding_completed';

export function OnboardingTour({ onComplete, onSkip, forceShow = false }: OnboardingTourProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
  const [isMounted, setIsMounted] = useState(false);

  const step = TOUR_STEPS[currentStep];
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === TOUR_STEPS.length - 1;

  // Check if tour should be shown
  useEffect(() => {
    setIsMounted(true);
    if (forceShow) {
      setIsVisible(true);
      return;
    }
    
    const completed = localStorage.getItem(STORAGE_KEY);
    if (!completed) {
      // Delay to let the UI render first
      const timer = setTimeout(() => setIsVisible(true), 1000);
      return () => clearTimeout(timer);
    }
  }, [forceShow]);

  // Update target element position
  useEffect(() => {
    if (!isVisible || !step.target) {
      setTargetRect(null);
      return;
    }

    const updatePosition = () => {
      const element = document.querySelector(step.target!);
      if (element) {
        setTargetRect(element.getBoundingClientRect());
      } else {
        setTargetRect(null);
      }
    };

    updatePosition();
    window.addEventListener('resize', updatePosition);
    window.addEventListener('scroll', updatePosition);

    return () => {
      window.removeEventListener('resize', updatePosition);
      window.removeEventListener('scroll', updatePosition);
    };
  }, [isVisible, step.target, currentStep]);

  const handleNext = useCallback(() => {
    if (isLastStep) {
      handleComplete();
    } else {
      setCurrentStep((prev) => prev + 1);
    }
  }, [isLastStep]);

  const handlePrev = useCallback(() => {
    setCurrentStep((prev) => Math.max(0, prev - 1));
  }, []);

  const handleSkip = useCallback(() => {
    localStorage.setItem(STORAGE_KEY, 'skipped');
    setIsVisible(false);
    onSkip?.();
  }, [onSkip]);

  const handleComplete = useCallback(() => {
    localStorage.setItem(STORAGE_KEY, 'completed');
    setIsVisible(false);
    onComplete?.();
  }, [onComplete]);

  // Keyboard navigation
  useEffect(() => {
    if (!isVisible) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowRight':
        case 'Enter':
          handleNext();
          break;
        case 'ArrowLeft':
          handlePrev();
          break;
        case 'Escape':
          handleSkip();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isVisible, handleNext, handlePrev, handleSkip]);

  if (!isMounted || !isVisible) return null;

  // Calculate tooltip position
  const getTooltipStyle = (): React.CSSProperties => {
    if (!targetRect || step.position === 'center') {
      return {
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
      };
    }

    const padding = 16;
    const tooltipWidth = 380;
    const tooltipHeight = 200;

    switch (step.position) {
      case 'right':
        return {
          position: 'fixed',
          top: targetRect.top + targetRect.height / 2 - tooltipHeight / 2,
          left: targetRect.right + padding,
        };
      case 'left':
        return {
          position: 'fixed',
          top: targetRect.top + targetRect.height / 2 - tooltipHeight / 2,
          left: targetRect.left - tooltipWidth - padding,
        };
      case 'bottom':
        return {
          position: 'fixed',
          top: targetRect.bottom + padding,
          left: targetRect.left + targetRect.width / 2 - tooltipWidth / 2,
        };
      case 'top':
        return {
          position: 'fixed',
          top: targetRect.top - tooltipHeight - padding,
          left: targetRect.left + targetRect.width / 2 - tooltipWidth / 2,
        };
      default:
        return {};
    }
  };

  return createPortal(
    <div className="fixed inset-0 z-[10000]" role="dialog" aria-modal="true" aria-label="Onboarding tour">
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Highlight cutout */}
      {targetRect && (
        <div
          className="absolute border-2 border-primary rounded-lg shadow-[0_0_0_9999px_rgba(0,0,0,0.6)] transition-all duration-300"
          style={{
            top: targetRect.top - 8,
            left: targetRect.left - 8,
            width: targetRect.width + 16,
            height: targetRect.height + 16,
          }}
        >
          {/* Pulse animation */}
          <div className="absolute inset-0 border-2 border-primary rounded-lg animate-ping opacity-50" />
        </div>
      )}

      {/* Tooltip */}
      <Card
        className={cn(
          'w-[380px] p-0 shadow-2xl border-primary/20',
          'animate-in fade-in zoom-in-95 duration-300'
        )}
        style={getTooltipStyle()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-muted/30">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              {step.icon}
            </div>
            <div>
              <Badge variant="secondary" className="text-xs mb-1">
                {currentStep + 1} / {TOUR_STEPS.length}
              </Badge>
              <h3 className="font-semibold text-sm">{step.title}</h3>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            onClick={handleSkip}
            aria-label="Skip tour"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-4">
          <p className="text-sm text-muted-foreground leading-relaxed">
            {step.description}
          </p>
          
          {step.action && (
            <div className="mt-3 p-3 rounded-lg bg-primary/5 border border-primary/10">
              <div className="flex items-center gap-2 text-xs text-primary font-medium">
                <Zap className="h-3.5 w-3.5" />
                {step.action}
              </div>
            </div>
          )}
        </div>

        {/* Progress dots */}
        <div className="flex justify-center gap-1.5 pb-3">
          {TOUR_STEPS.map((_, index) => (
            <button
              key={index}
              className={cn(
                'w-2 h-2 rounded-full transition-all',
                index === currentStep
                  ? 'bg-primary w-4'
                  : index < currentStep
                  ? 'bg-primary/50'
                  : 'bg-muted-foreground/30'
              )}
              onClick={() => setCurrentStep(index)}
              aria-label={`Go to step ${index + 1}`}
            />
          ))}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t bg-muted/30">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleSkip}
            className="text-muted-foreground"
          >
            건너뛰기
          </Button>
          
          <div className="flex gap-2">
            {!isFirstStep && (
              <Button variant="outline" size="sm" onClick={handlePrev}>
                <ChevronLeft className="h-4 w-4 mr-1" />
                이전
              </Button>
            )}
            <Button size="sm" onClick={handleNext}>
              {isLastStep ? '시작하기' : '다음'}
              {!isLastStep && <ChevronRight className="h-4 w-4 ml-1" />}
            </Button>
          </div>
        </div>
      </Card>
    </div>,
    document.body
  );
}

// Hook to control tour programmatically
export function useOnboardingTour() {
  const [showTour, setShowTour] = useState(false);

  const startTour = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setShowTour(true);
  }, []);

  const resetTour = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  return { showTour, setShowTour, startTour, resetTour };
}
