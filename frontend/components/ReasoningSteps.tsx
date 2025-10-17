'use client';

import React, { useState, useEffect, useRef } from 'react';
import { AgentStep } from '@/lib/types';

interface ReasoningStepsProps {
  steps: AgentStep[];
  isProcessing?: boolean;
}

const ReasoningSteps: React.FC<ReasoningStepsProps> = ({ steps, isProcessing = false }) => {
  const [isExpanded, setIsExpanded] = useState(true); // Auto-expand for better visibility
  const [highlightedIndex, setHighlightedIndex] = useState<number | null>(null);
  const stepsEndRef = useRef<HTMLDivElement>(null);
  const prevStepsLengthRef = useRef(steps.length);

  // Auto-scroll to latest step
  useEffect(() => {
    if (steps.length > prevStepsLengthRef.current && isExpanded) {
      stepsEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      
      // Highlight the new step
      setHighlightedIndex(steps.length - 1);
      const timer = setTimeout(() => setHighlightedIndex(null), 2000);
      return () => clearTimeout(timer);
    }
    prevStepsLengthRef.current = steps.length;
  }, [steps.length, isExpanded]);

  if (steps.length === 0) {
    return null;
  }

  const getStepIcon = (type: string) => {
    switch (type) {
      case 'thought':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
            <path
              fillRule="evenodd"
              d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'action':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'planning':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
            <path
              fillRule="evenodd"
              d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm9.707 5.707a1 1 0 00-1.414-1.414L9 12.586l-1.293-1.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'reflection':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'memory':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 2a2 2 0 00-2 2v8a2 2 0 002 2h6a2 2 0 002-2V6.414A2 2 0 0016.414 5L14 2.586A2 2 0 0012.586 2H9z" />
            <path d="M3 8a2 2 0 012-2v10h8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
          </svg>
        );
      case 'error':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
              clipRule="evenodd"
            />
          </svg>
        );
    }
  };

  const getStepColor = (type: string) => {
    switch (type) {
      case 'thought':
        return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20';
      case 'action':
        return 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20';
      case 'planning':
        return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20';
      case 'reflection':
        return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20';
      case 'memory':
        return 'text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/20';
      case 'error':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20';
      default:
        return 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900/20';
    }
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden shadow-sm">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-between hover:from-gray-100 hover:to-gray-200 dark:hover:from-gray-800 dark:hover:to-gray-700 transition-all duration-200"
      >
        <div className="flex items-center gap-3">
          <svg
            className={`w-4 h-4 transition-transform duration-300 ${
              isExpanded ? 'transform rotate-90' : ''
            }`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
              clipRule="evenodd"
            />
          </svg>
          <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">
            🧠 Reasoning Steps
          </span>
          <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full">
            {steps.length}
          </span>
          {isProcessing && (
            <span className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400">
              <svg className="animate-spin h-3 w-3" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Processing...
            </span>
          )}
        </div>
        <span className="text-xs font-medium text-gray-600 dark:text-gray-400 px-2 py-1 rounded hover:bg-white/50 dark:hover:bg-black/20 transition-colors">
          {isExpanded ? '▼ Hide' : '▶ Show'}
        </span>
      </button>

      {isExpanded && (
        <div className="p-4 space-y-2 max-h-[500px] overflow-y-auto bg-gray-50/50 dark:bg-gray-900/50">
          {steps.map((step, index) => (
            <div
              key={`${step.step_id}-${index}`}
              className={`
                flex gap-3 p-3 rounded-lg transition-all duration-500
                ${getStepColor(step.type)}
                ${highlightedIndex === index ? 'ring-2 ring-blue-400 dark:ring-blue-600 scale-[1.02]' : ''}
                ${index === steps.length - 1 && isProcessing ? 'animate-pulse' : ''}
                transform hover:scale-[1.01] hover:shadow-md
              `}
              style={{
                animation: `fadeInSlide 0.5s ease-out ${index * 0.1}s both`
              }}
            >
              <div className="flex-shrink-0 mt-0.5">
                <div className={`
                  p-1.5 rounded-full
                  ${index === steps.length - 1 && isProcessing ? 'animate-bounce' : ''}
                `}>
                  {getStepIcon(step.type)}
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-xs font-bold uppercase tracking-wide">
                    {step.type}
                  </span>
                  {step.metadata?.action && (
                    <span className="text-xs opacity-75 font-medium">
                      • {step.metadata.action}
                    </span>
                  )}
                  {index === steps.length - 1 && isProcessing && (
                    <span className="ml-auto text-xs text-blue-600 dark:text-blue-400 font-medium animate-pulse">
                      ● Live
                    </span>
                  )}
                </div>
                <p className="text-sm whitespace-pre-wrap break-words leading-relaxed overflow-hidden text-ellipsis">
                  {step.content || ''}
                </p>
                {step.metadata && Object.keys(step.metadata).length > 0 && (
                  <details className="mt-2 group">
                    <summary className="text-xs cursor-pointer opacity-75 hover:opacity-100 font-medium transition-opacity">
                      📋 Metadata
                    </summary>
                    <pre className="text-xs mt-2 p-2 bg-black/10 dark:bg-white/10 rounded overflow-x-auto border border-black/10 dark:border-white/10">
                      {JSON.stringify(step.metadata, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            </div>
          ))}
          <div ref={stepsEndRef} />
        </div>
      )}
      
      <style jsx>{`
        @keyframes fadeInSlide {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
};

export default ReasoningSteps;
