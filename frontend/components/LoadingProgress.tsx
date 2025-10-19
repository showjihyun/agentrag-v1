'use client';

import React, { useState, useEffect } from 'react';

interface LoadingProgressProps {
  stage?: 'analyzing' | 'searching' | 'generating' | 'finalizing';
  message?: string;
  showProgress?: boolean;
  className?: string;
  isWebSearch?: boolean;
  elapsedTime?: number;
}

/**
 * Loading Progress Component
 * 
 * Shows clear loading states with progress indication and stage information.
 */
export default function LoadingProgress({
  stage = 'analyzing',
  message,
  showProgress = true,
  className = '',
  isWebSearch = false,
  elapsedTime = 0
}: LoadingProgressProps) {
  const [progress, setProgress] = useState(0);

  // Simulate progress based on stage
  useEffect(() => {
    const stageProgress = {
      analyzing: 25,
      searching: 50,
      generating: 75,
      finalizing: 90
    };

    const targetProgress = stageProgress[stage];
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= targetProgress) {
          clearInterval(interval);
          return targetProgress;
        }
        return Math.min(prev + 1, targetProgress);
      });
    }, 50);

    return () => clearInterval(interval);
  }, [stage]);

  const stageInfo = {
    analyzing: {
      icon: '🔍',
      title: isWebSearch ? 'Web Search' : 'Analyzing',
      description: isWebSearch 
        ? '🌐 Searching the web... (5-15 seconds expected)'
        : 'Understanding your question...'
    },
    searching: {
      icon: isWebSearch ? '🌐' : '📚',
      title: isWebSearch ? 'Web Search' : 'Searching',
      description: isWebSearch
        ? '🔎 Finding information from the internet...'
        : 'Finding relevant information...'
    },
    generating: {
      icon: '✍️',
      title: 'Generating Answer',
      description: isWebSearch
        ? '🤖 AI is analyzing web results and writing your answer...'
        : 'Crafting your answer...'
    },
    finalizing: {
      icon: '✨',
      title: 'Finalizing',
      description: 'Almost done...'
    }
  };

  const currentStage = stageInfo[stage];
  
  // Estimate remaining time for web search
  const estimatedTotal = isWebSearch ? 15 : 10;
  const remainingTime = Math.max(0, estimatedTotal - elapsedTime);

  return (
    <div className={`bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 ${className}`}>
      <div className="flex items-start gap-3">
        {/* Animated Icon */}
        <div className="flex-shrink-0 text-2xl animate-bounce">
          {currentStage.icon}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Title */}
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-sm font-semibold text-blue-800 dark:text-blue-300">
              {currentStage.title}
            </h4>
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0ms' }}></span>
              <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '150ms' }}></span>
              <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '300ms' }}></span>
            </div>
          </div>

          {/* Description */}
          <p className="text-sm text-blue-700 dark:text-blue-400 mb-2">
            {message || currentStage.description}
          </p>
          
          {/* Elapsed Time */}
          {elapsedTime > 0 && (
            <p className="text-xs text-blue-600 dark:text-blue-500 mb-3">
              ⏱️ {elapsedTime}s elapsed
              {isWebSearch && remainingTime > 0 && (
                <span className="ml-2 text-blue-500">
                  (≈{remainingTime}s remaining)
                </span>
              )}
            </p>
          )}

          {/* Progress Bar */}
          {showProgress && (
            <div className="space-y-1">
              <div className="w-full bg-blue-200 dark:bg-blue-900/40 rounded-full h-2 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${progress}%` }}
                >
                  <div className="h-full w-full bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"></div>
                </div>
              </div>
              <p className="text-xs text-blue-600 dark:text-blue-500 text-right">
                {progress}%
              </p>
            </div>
          )}
        </div>
      </div>

      {/* CSS for shimmer animation */}
      <style jsx>{`
        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }

        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
      `}</style>
    </div>
  );
}
