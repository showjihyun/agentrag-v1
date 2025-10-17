'use client';

import React from 'react';

interface Highlight {
  type: 'exact' | 'fuzzy' | 'semantic';
  matched_phrase: string;
  start: number;
  end: number;
  text: string;
  context: string;
  score: number;
}

interface Source {
  document_id: string;
  document_name?: string;
  text: string;
  score: number;
  highlights?: Highlight[];
  highlight_count?: number;
}

interface SourceHighlightProps {
  sources: Source[];
  maxSources?: number;
  showContext?: boolean;
}

export const SourceHighlight: React.FC<SourceHighlightProps> = ({
  sources,
  maxSources = 5,
  showContext = true,
}) => {
  if (!sources || sources.length === 0) {
    return null;
  }

  const displaySources = sources.slice(0, maxSources);

  const renderHighlightedText = (source: Source) => {
    const text = source.text;
    const highlights = source.highlights || [];

    if (highlights.length === 0) {
      return <p className="text-sm text-gray-700 dark:text-gray-300">{text}</p>;
    }

    // Sort highlights by position
    const sortedHighlights = [...highlights].sort((a, b) => a.start - b.start);

    // Build segments
    const segments: React.ReactNode[] = [];
    let lastPos = 0;

    sortedHighlights.forEach((highlight, idx) => {
      // Add text before highlight
      if (highlight.start > lastPos) {
        segments.push(
          <span key={`text-${idx}`}>
            {text.substring(lastPos, highlight.start)}
          </span>
        );
      }

      // Add highlighted text
      segments.push(
        <mark
          key={`highlight-${idx}`}
          className={`
            px-1 rounded
            ${highlight.type === 'exact' 
              ? 'bg-yellow-200 dark:bg-yellow-800' 
              : 'bg-blue-200 dark:bg-blue-800'
            }
            hover:bg-yellow-300 dark:hover:bg-yellow-700
            transition-colors cursor-help
          `}
          title={`Match: ${highlight.matched_phrase} (Score: ${highlight.score.toFixed(2)})`}
        >
          {text.substring(highlight.start, highlight.end)}
        </mark>
      );

      lastPos = highlight.end;
    });

    // Add remaining text
    if (lastPos < text.length) {
      segments.push(
        <span key="text-end">
          {text.substring(lastPos)}
        </span>
      );
    }

    return (
      <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
        {segments}
      </p>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          📚 Source Documents
        </h3>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          {sources.length} sources
        </span>
      </div>

      <div className="space-y-3">
        {displaySources.map((source, idx) => (
          <div
            key={source.document_id || idx}
            className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-800 hover:shadow-md transition-shadow"
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                  #{idx + 1}
                </span>
                {source.document_name && (
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {source.document_name}
                  </span>
                )}
              </div>
              
              <div className="flex items-center gap-2">
                {/* Highlight count badge */}
                {source.highlight_count && source.highlight_count > 0 && (
                  <span className="px-2 py-1 text-xs font-medium bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 rounded-full">
                    {source.highlight_count} highlights
                  </span>
                )}
                
                {/* Relevance score */}
                <span className="px-2 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full">
                  {(source.score * 100).toFixed(0)}% relevant
                </span>
              </div>
            </div>

            {/* Content with highlights */}
            <div className="prose prose-sm dark:prose-invert max-w-none">
              {renderHighlightedText(source)}
            </div>

            {/* Highlight details (optional) */}
            {showContext && source.highlights && source.highlights.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                <details className="text-xs text-gray-600 dark:text-gray-400">
                  <summary className="cursor-pointer hover:text-gray-900 dark:hover:text-gray-200">
                    Show highlight details
                  </summary>
                  <div className="mt-2 space-y-2">
                    {source.highlights.map((highlight, hIdx) => (
                      <div key={hIdx} className="pl-3 border-l-2 border-yellow-400 dark:border-yellow-600">
                        <div className="font-medium">
                          {highlight.type === 'exact' ? '🎯 Exact' : '🔍 Fuzzy'} Match
                        </div>
                        <div>Phrase: "{highlight.matched_phrase}"</div>
                        <div>Score: {highlight.score.toFixed(2)}</div>
                      </div>
                    ))}
                  </div>
                </details>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400 pt-2">
        <div className="flex items-center gap-1">
          <span className="inline-block w-4 h-4 bg-yellow-200 dark:bg-yellow-800 rounded"></span>
          <span>Exact match</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="inline-block w-4 h-4 bg-blue-200 dark:bg-blue-800 rounded"></span>
          <span>Fuzzy match</span>
        </div>
      </div>
    </div>
  );
};

export default SourceHighlight;
