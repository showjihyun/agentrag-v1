'use client';

import React, { useState } from 'react';

interface ResponseComparisonProps {
  currentContent: string;
  previousContent?: string;
  responseType?: 'preliminary' | 'refinement' | 'final';
}

const ResponseComparison: React.FC<ResponseComparisonProps> = ({
  currentContent,
  previousContent,
  responseType,
}) => {
  const [showComparison, setShowComparison] = useState(false);

  // Only show toggle if we have previous content and it's different
  if (!previousContent || previousContent === currentContent || responseType === 'preliminary') {
    return (
      <div className="prose prose-sm dark:prose-invert max-w-none">
        <p className="whitespace-pre-wrap">{currentContent}</p>
      </div>
    );
  }

  // Simple diff highlighting
  const getDiffHighlight = (text: string, isOld: boolean) => {
    if (!previousContent) return text;
    
    // If current is longer, highlight the new part
    if (!isOld && text.length > previousContent.length) {
      const oldPart = text.slice(0, previousContent.length);
      const newPart = text.slice(previousContent.length);
      return (
        <>
          {oldPart}
          <span className="bg-green-200 dark:bg-green-800/50 px-1 rounded">
            {newPart}
          </span>
        </>
      );
    }
    
    return text;
  };

  return (
    <div className="space-y-2">
      <button
        onClick={() => setShowComparison(!showComparison)}
        className="inline-flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 hover:underline focus:outline-none"
      >
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
        </svg>
        {showComparison ? 'Hide comparison' : 'Compare versions'}
      </button>

      {showComparison ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs font-medium text-gray-600 dark:text-gray-400">
              <span className="inline-block w-2 h-2 rounded-full bg-yellow-500"></span>
              Initial Response
            </div>
            <div className="prose prose-sm dark:prose-invert max-w-none bg-gray-50 dark:bg-gray-800/50 rounded p-2">
              <p className="whitespace-pre-wrap text-sm">{previousContent}</p>
            </div>
          </div>
          
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs font-medium text-gray-600 dark:text-gray-400">
              <span className="inline-block w-2 h-2 rounded-full bg-green-500"></span>
              Refined Response
            </div>
            <div className="prose prose-sm dark:prose-invert max-w-none bg-gray-50 dark:bg-gray-800/50 rounded p-2">
              <p className="whitespace-pre-wrap text-sm">
                {getDiffHighlight(currentContent, false)}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <p className="whitespace-pre-wrap">{currentContent}</p>
        </div>
      )}
    </div>
  );
};

export default ResponseComparison;
