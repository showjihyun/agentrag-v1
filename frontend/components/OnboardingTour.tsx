'use client';

import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Button } from './Button';

interface TourStep {
  target: string;
  title: string;
  content: string;
  placement?: 'top' | 'bottom' | 'left' | 'right';
}

interface OnboardingTourProps {
  steps: TourStep[];
  onComplete: () => void;
  onSkip: () => void;
}

export default function OnboardingTour({ steps, onComplete, onSkip }: OnboardingTourProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (currentStep < steps.length) {
      updatePosition();
      setIsVisible(true);
    }
  }, [currentStep]);

  const updatePosition = () => {
    const step = steps[currentStep];
    const element = document.querySelector(step.target);
    
    if (element) {
      const rect = element.getBoundingClientRect();
      const placement = step.placement || 'bottom';
      
      let top = 0;
      let left = 0;
      
      switch (placement) {
        case 'bottom':
          top = rect.bottom + window.scrollY + 10;
          left = rect.left + window.scrollX + rect.width / 2;
          break;
        case 'top':
          top = rect.top + window.scrollY - 10;
          left = rect.left + window.scrollX + rect.width / 2;
          break;
        case 'left':
          top = rect.top + window.scrollY + rect.height / 2;
          left = rect.left + window.scrollX - 10;
          break;
        case 'right':
          top = rect.top + window.scrollY + rect.height / 2;
          left = rect.right + window.scrollX + 10;
          break;
      }
      
      setPosition({ top, left });
      
      // Highlight element
      element.classList.add('onboarding-highlight');
      
      // Scroll into view
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  const handleNext = () => {
    // Remove highlight from current element
    const currentElement = document.querySelector(steps[currentStep].target);
    if (currentElement) {
      currentElement.classList.remove('onboarding-highlight');
    }
    
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      const currentElement = document.querySelector(steps[currentStep].target);
      if (currentElement) {
        currentElement.classList.remove('onboarding-highlight');
      }
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    const currentElement = document.querySelector(steps[currentStep].target);
    if (currentElement) {
      currentElement.classList.remove('onboarding-highlight');
    }
    setIsVisible(false);
    onComplete();
  };

  const handleSkip = () => {
    const currentElement = document.querySelector(steps[currentStep].target);
    if (currentElement) {
      currentElement.classList.remove('onboarding-highlight');
    }
    setIsVisible(false);
    onSkip();
  };

  if (!isVisible || currentStep >= steps.length) {
    return null;
  }

  const step = steps[currentStep];
  const placement = step.placement || 'bottom';

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/50 z-[9998]" onClick={handleSkip} />
      
      {/* Tour Card */}
      <div
        className={cn(
          'fixed z-[9999] bg-white dark:bg-gray-800 rounded-lg shadow-2xl p-6 max-w-sm',
          placement === 'bottom' && '-translate-x-1/2',
          placement === 'top' && '-translate-x-1/2 -translate-y-full',
          placement === 'left' && '-translate-x-full -translate-y-1/2',
          placement === 'right' && '-translate-y-1/2'
        )}
        style={{ top: `${position.top}px`, left: `${position.left}px` }}
      >
        {/* Arrow */}
        <div
          className={cn(
            'absolute w-3 h-3 bg-white dark:bg-gray-800 rotate-45',
            placement === 'bottom' && 'top-0 left-1/2 -translate-x-1/2 -translate-y-1/2',
            placement === 'top' && 'bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2',
            placement === 'left' && 'right-0 top-1/2 -translate-y-1/2 translate-x-1/2',
            placement === 'right' && 'left-0 top-1/2 -translate-y-1/2 -translate-x-1/2'
          )}
        />
        
        {/* Content */}
        <div className="relative">
          <div className="flex items-start justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {step.title}
            </h3>
            <button
              onClick={handleSkip}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              aria-label="Skip tour"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {step.content}
          </p>
          
          {/* Progress */}
          <div className="flex items-center gap-2 mb-4">
            {steps.map((_, index) => (
              <div
                key={index}
                className={cn(
                  'h-1.5 rounded-full flex-1 transition-colors',
                  index === currentStep
                    ? 'bg-blue-600'
                    : index < currentStep
                    ? 'bg-blue-400'
                    : 'bg-gray-300 dark:bg-gray-600'
                )}
              />
            ))}
          </div>
          
          {/* Navigation */}
          <div className="flex items-center justify-between">
            <Button
              onClick={handlePrevious}
              disabled={currentStep === 0}
              variant="ghost"
              size="sm"
            >
              Previous
            </Button>
            
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {currentStep + 1} / {steps.length}
            </span>
            
            <Button
              onClick={handleNext}
              variant="primary"
              size="sm"
            >
              {currentStep === steps.length - 1 ? 'Finish' : 'Next'}
            </Button>
          </div>
        </div>
      </div>
      
      {/* Global styles for highlighting */}
      <style jsx global>{`
        .onboarding-highlight {
          position: relative;
          z-index: 9997;
          box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.5);
          border-radius: 8px;
          animation: pulse-highlight 2s infinite;
        }
        
        @keyframes pulse-highlight {
          0%, 100% {
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.5);
          }
          50% {
            box-shadow: 0 0 0 8px rgba(59, 130, 246, 0.3);
          }
        }
      `}</style>
    </>
  );
}
