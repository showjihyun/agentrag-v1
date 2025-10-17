'use client';

import React, { useState } from 'react';
import { SearchResult } from '@/lib/types';

interface Highlight {
  type: 'exact' | 'fuzzy' | 'semantic';
  matched_phrase: string;
  start: number;
  end: number;
  text: string;
  context: string;
  score: number;
}

interface SourceWithHighlights extends SearchResult {
  highlights?: Highlight[];
  highlight_count?: number;
}

interface SourceCitationsProps {
  sources: SearchResult[];
}

const SourceCitations: React.FC<SourceCitationsProps> = ({ sources }) => {
  const [isExpanded, setIsExpanded] = useState(false); // Overall expand/collapse - default hidden for better chat space
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());

  if (sources.length === 0) {
    return null;
  }

  const toggleSource = (chunkId: string) => {
    setExpandedSources((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(chunkId)) {
        newSet.delete(chunkId);
      } else {
        newSet.add(chunkId);
      }
      return newSet;
    });
  };

  const highlightRelevantText = (text: string, maxLength: number = 200) => {
    if (text.length <= maxLength) {
      return text;
    }
    return text.substring(0, maxLength) + '...';
  };

  const renderHighlightedText = (source: SourceWithHighlights) => {
    const text = source.text || '';
    const highlights = source.highlights || [];

    if (highlights.length === 0) {
      return <span className="whitespace-pre-wrap break-words">{text}</span>;
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
      const highlightClass = highlight.type === 'exact' 
        ? 'bg-yellow-200 dark:bg-yellow-800/60' 
        : 'bg-blue-200 dark:bg-blue-800/60';
      
      segments.push(
        <mark
          key={`highlight-${idx}`}
          className={`${highlightClass} px-1 rounded hover:bg-yellow-300 dark:hover:bg-yellow-700/80 transition-colors cursor-help`}
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

    return <span className="whitespace-pre-wrap break-words">{segments}</span>;
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 dark:text-green-400';
    if (score >= 0.6) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-orange-600 dark:text-orange-400';
  };

  const getScoreBadge = (score: number) => {
    if (score >= 0.8) return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300';
    if (score >= 0.6) return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300';
    return 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300';
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
          <svg
            className="w-5 h-5 text-gray-600 dark:text-gray-400"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
          </svg>
          <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">
            📚 Sources
          </span>
          <span className="px-2 py-0.5 text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded-full">
            {sources.length}
          </span>
        </div>
        <span className="text-xs font-medium text-gray-600 dark:text-gray-400 px-2 py-1 rounded hover:bg-white/50 dark:hover:bg-black/20 transition-colors">
          {isExpanded ? '▼ Hide' : '▶ Show'}
        </span>
      </button>

      {isExpanded && (
        <div className="divide-y divide-gray-200 dark:divide-gray-700 bg-gray-50/50 dark:bg-gray-900/50 max-h-[600px] overflow-y-auto">
        {sources.map((source, index) => {
          const isSourceExpanded = expandedSources.has(source.chunk_id);
          
          return (
            <div
              key={`${source.chunk_id}-${index}`}
              className="p-4 hover:bg-white dark:hover:bg-gray-800 transition-all duration-200"
              style={{
                animation: `fadeInSlide 0.3s ease-out ${index * 0.05}s both`
              }}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100 break-words max-w-full">
                      [{index + 1}] {source.document_name || 'Unknown Document'}
                    </span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${getScoreBadge(
                        source.score
                      )}`}
                    >
                      {(source.score * 100).toFixed(0)}% match
                    </span>
                    {(source as SourceWithHighlights).highlight_count && (source as SourceWithHighlights).highlight_count! > 0 && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300">
                        ✨ {(source as SourceWithHighlights).highlight_count} highlights
                      </span>
                    )}
                  </div>

                  <div className="text-sm text-gray-700 dark:text-gray-300 break-words overflow-hidden">
                    {isSourceExpanded ? (
                      <div className="space-y-2">
                        <div className="whitespace-pre-wrap break-words leading-relaxed">
                          {renderHighlightedText(source as SourceWithHighlights)}
                        </div>
                        {(source as SourceWithHighlights).highlights && (source as SourceWithHighlights).highlights!.length > 0 && (
                          <details className="mt-2">
                            <summary className="text-xs cursor-pointer text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300">
                              Show highlight details
                            </summary>
                            <div className="mt-2 space-y-2">
                              {(source as SourceWithHighlights).highlights!.map((highlight, hIdx) => (
                                <div key={hIdx} className="pl-3 border-l-2 border-yellow-400 dark:border-yellow-600 text-xs">
                                  <div className="font-medium">
                                    {highlight.type === 'exact' ? '🎯 Exact' : '🔍 Fuzzy'} Match
                                  </div>
                                  <div className="text-gray-600 dark:text-gray-400">
                                    Phrase: "{highlight.matched_phrase.substring(0, 50)}{highlight.matched_phrase.length > 50 ? '...' : ''}"
                                  </div>
                                  <div className="text-gray-600 dark:text-gray-400">
                                    Score: {highlight.score.toFixed(2)}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </details>
                        )}
                        {source.metadata && Object.keys(source.metadata).length > 0 && (
                          <details className="mt-2">
                            <summary className="text-xs cursor-pointer text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300">
                              Document metadata
                            </summary>
                            <div className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs">
                              {Object.entries(source.metadata).map(([key, value]) => (
                                <div key={key} className="flex gap-2">
                                  <span className="font-medium">{key}:</span>
                                  <span>{String(value)}</span>
                                </div>
                              ))}
                            </div>
                          </details>
                        )}
                      </div>
                    ) : (
                      <p className="line-clamp-3 break-words overflow-hidden">
                        {highlightRelevantText(source.text || '')}
                      </p>
                    )}
                  </div>
                </div>

                <button
                  onClick={() => toggleSource(source.chunk_id)}
                  className="flex-shrink-0 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 text-xs font-medium transition-colors"
                >
                  {isSourceExpanded ? (
                    <div className="flex items-center gap-1">
                      <span>Show less</span>
                      <svg
                        className="w-4 h-4"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1">
                      <span>Show more</span>
                      <svg
                        className="w-4 h-4"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
      )}

      {/* Highlight Legend */}
      {isExpanded && sources.some(s => (s as SourceWithHighlights).highlight_count && (s as SourceWithHighlights).highlight_count! > 0) && (
        <div className="px-4 py-2 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-4 text-xs text-gray-600 dark:text-gray-400">
            <span className="font-medium">Legend:</span>
            <div className="flex items-center gap-1">
              <span className="inline-block w-4 h-4 bg-yellow-200 dark:bg-yellow-800/60 rounded"></span>
              <span>Exact match</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="inline-block w-4 h-4 bg-blue-200 dark:bg-blue-800/60 rounded"></span>
              <span>Fuzzy match</span>
            </div>
          </div>
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
        
        /* Custom scrollbar styling */
        .divide-y::-webkit-scrollbar {
          width: 8px;
        }
        
        .divide-y::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.05);
          border-radius: 4px;
        }
        
        .divide-y::-webkit-scrollbar-thumb {
          background: rgba(0, 0, 0, 0.2);
          border-radius: 4px;
        }
        
        .divide-y::-webkit-scrollbar-thumb:hover {
          background: rgba(0, 0, 0, 0.3);
        }
        
        /* Dark mode scrollbar */
        :global(.dark) .divide-y::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
        }
        
        :global(.dark) .divide-y::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
        }
        
        :global(.dark) .divide-y::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      `}</style>
    </div>
  );
};

export default SourceCitations;
