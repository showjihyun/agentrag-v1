'use client';

import React from 'react';

interface ResponseStatusBadgeProps {
  responseType?: 'preliminary' | 'refinement' | 'final';
  pathSource?: 'speculative' | 'agentic' | 'hybrid';
  confidenceScore?: number;
  isRefining?: boolean;
}

const ResponseStatusBadge: React.FC<ResponseStatusBadgeProps> = ({
  responseType,
  pathSource,
  confidenceScore,
  isRefining,
}) => {
  if (!responseType) return null;

  const getBadgeStyles = () => {
    switch (responseType) {
      case 'preliminary':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'refinement':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'final':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const getBadgeIcon = () => {
    switch (responseType) {
      case 'preliminary':
        return (
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
          </svg>
        );
      case 'refinement':
        return (
          <svg className="w-3 h-3 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
          </svg>
        );
      case 'final':
        return (
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  const getBadgeText = () => {
    switch (responseType) {
      case 'preliminary':
        return 'Preliminary';
      case 'refinement':
        return isRefining ? 'Refining...' : 'Refined';
      case 'final':
        return 'Complete';
      default:
        return '';
    }
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 dark:text-green-400';
    if (score >= 0.6) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-orange-600 dark:text-orange-400';
  };

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getBadgeStyles()}`}>
        {getBadgeIcon()}
        {getBadgeText()}
      </span>
      
      {confidenceScore !== undefined && (
        <span className={`text-xs font-medium ${getConfidenceColor(confidenceScore)}`}>
          Confidence: {(confidenceScore * 100).toFixed(0)}%
        </span>
      )}
      
      {pathSource && (
        <span className="text-xs text-gray-500 dark:text-gray-400">
          via {pathSource}
        </span>
      )}
      
      {isRefining && (
        <span className="inline-flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400">
          <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Processing deeper analysis...
        </span>
      )}
    </div>
  );
};

export default ResponseStatusBadge;
