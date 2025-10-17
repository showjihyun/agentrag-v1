'use client';

import React, { useEffect, useState } from 'react';

interface RefinementHighlightProps {
  content: string;
  previousContent?: string;
  isRefining?: boolean;
  className?: string;
}

const RefinementHighlight: React.FC<RefinementHighlightProps> = ({
  content,
  previousContent,
  isRefining,
  className = '',
}) => {
  const [showHighlight, setShowHighlight] = useState(false);

  useEffect(() => {
    // Trigger highlight animation when content changes
    if (previousContent && content !== previousContent) {
      setShowHighlight(true);
      const timer = setTimeout(() => setShowHighlight(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [content, previousContent]);

  // Simple diff detection - highlight new content
  const hasNewContent = previousContent && content.length > previousContent.length;

  return (
    <div className={`relative ${className}`}>
      <div
        className={`prose prose-sm dark:prose-invert max-w-none transition-all duration-300 ${
          showHighlight ? 'bg-blue-50 dark:bg-blue-900/20 rounded p-2' : ''
        }`}
      >
        <p className="whitespace-pre-wrap">
          {previousContent && hasNewContent ? (
            <>
              <span>{previousContent}</span>
              <span
                className={`${
                  showHighlight
                    ? 'bg-yellow-200 dark:bg-yellow-700/50 animate-pulse'
                    : ''
                } transition-colors duration-500`}
              >
                {content.slice(previousContent.length)}
              </span>
            </>
          ) : (
            content
          )}
        </p>
      </div>
      
      {isRefining && (
        <div className="absolute -right-2 -top-2">
          <div className="relative">
            <span className="flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default RefinementHighlight;
