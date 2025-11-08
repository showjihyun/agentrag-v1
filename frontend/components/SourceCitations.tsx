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
  onChunkClick?: (chunkId: string) => void;
}

const SourceCitations: React.FC<SourceCitationsProps> = ({ sources, onChunkClick }) => {
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

      // Add highlighted text with enhanced styling
      const highlightClass = highlight.type === 'exact' 
        ? 'bg-gradient-to-r from-yellow-200 via-yellow-300 to-yellow-200 dark:from-yellow-800/70 dark:via-yellow-700/80 dark:to-yellow-800/70' 
        : 'bg-gradient-to-r from-blue-200 via-blue-300 to-blue-200 dark:from-blue-800/70 dark:via-blue-700/80 dark:to-blue-800/70';
      
      const pulseAnimation = highlight.type === 'exact' ? 'animate-pulse-subtle' : '';
      
      segments.push(
        <mark
          key={`highlight-${idx}`}
          className={`${highlightClass} ${pulseAnimation} px-1.5 py-0.5 rounded-md font-medium shadow-sm hover:shadow-md hover:scale-105 transition-all duration-200 cursor-help border-b-2 ${highlight.type === 'exact' ? 'border-yellow-400 dark:border-yellow-600' : 'border-blue-400 dark:border-blue-600'}`}
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
    <div className="border-2 border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden shadow-md hover:shadow-xl transition-all duration-300 hover:border-blue-300 dark:hover:border-blue-600">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 bg-gradient-to-r from-blue-50 via-purple-50 to-pink-50 dark:from-gray-900 dark:via-gray-850 dark:to-gray-900 flex items-center justify-between hover:from-blue-100 hover:via-purple-100 hover:to-pink-100 dark:hover:from-gray-800 dark:hover:via-gray-750 dark:hover:to-gray-800 transition-all duration-300 group relative overflow-hidden"
      >
        {/* Animated background shimmer */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent dark:via-white/5 translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-1000"></div>
        
        <div className="relative z-10 w-full flex items-center justify-between">
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
          <span className="px-2.5 py-1 text-xs font-bold bg-gradient-to-r from-green-400 to-emerald-500 dark:from-green-600 dark:to-emerald-700 text-white rounded-full shadow-md hover:shadow-lg hover:scale-110 transition-all duration-200 animate-pulse-subtle">
            {sources.length}
          </span>
        </div>
        <span className="text-xs font-medium text-gray-600 dark:text-gray-400 px-3 py-1.5 rounded-lg hover:bg-white/70 dark:hover:bg-black/30 transition-all duration-200 hover:scale-105 flex items-center gap-1">
          {isExpanded ? (
            <>
              <span>Hide</span>
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
              </svg>
            </>
          ) : (
            <>
              <span>Show</span>
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </>
          )}
        </span>
        </div>
      </button>

      {isExpanded && (
        <div className="divide-y divide-gray-200 dark:divide-gray-700 bg-gray-50/50 dark:bg-gray-900/50 max-h-[600px] overflow-y-auto">
        {sources.map((source, index) => {
          const isSourceExpanded = expandedSources.has(source.chunk_id);
          
          return (
            <div
              key={`${source.chunk_id}-${index}`}
              className="p-4 hover:bg-white dark:hover:bg-gray-800 transition-all duration-200 hover:shadow-lg hover:scale-[1.01] relative group cursor-pointer"
              style={{
                animation: `fadeInSlide 0.3s ease-out ${index * 0.05}s both`
              }}
              onClick={() => {
                onChunkClick?.(source.chunk_id);
                // Visual feedback
                const element = document.getElementById(`chunk-${source.chunk_id}`);
                if (element) {
                  element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
              }}
            >
              {/* Decorative gradient border on hover */}
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 via-purple-500/0 to-pink-500/0 group-hover:from-blue-500/10 group-hover:via-purple-500/10 group-hover:to-pink-500/10 rounded-lg transition-all duration-300 pointer-events-none"></div>
              
              <div className="relative z-10">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100 break-words max-w-full flex items-center gap-2">
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-xs">
                        {index + 1}
                      </span>
                      {source.document_name || 'Unknown Document'}
                    </span>
                    <span
                      className={`text-xs px-2.5 py-1 rounded-full font-semibold shadow-sm hover:shadow-md transition-all duration-200 hover:scale-105 ${getScoreBadge(
                        source.score
                      )}`}
                    >
                      🎯 {(source.score * 100).toFixed(0)}% match
                    </span>
                    {(source as SourceWithHighlights).highlight_count && (source as SourceWithHighlights).highlight_count! > 0 && (
                      <span className="text-xs px-2.5 py-1 rounded-full bg-gradient-to-r from-yellow-200 to-amber-300 dark:from-yellow-800/50 dark:to-amber-700/50 text-yellow-900 dark:text-yellow-200 font-semibold shadow-sm hover:shadow-md transition-all duration-200 hover:scale-105 animate-pulse-subtle">
                        ✨ {(source as SourceWithHighlights).highlight_count} highlights
                      </span>
                    )}
                    <span className="text-xs px-2.5 py-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 font-medium hover:bg-blue-200 dark:hover:bg-blue-800/50 transition-all duration-200">
                      👁️ Click to view
                    </span>
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
            </div>
          );
        })}
      </div>
      )}

      {/* Highlight Legend */}
      {isExpanded && sources.some(s => (s as SourceWithHighlights).highlight_count && (s as SourceWithHighlights).highlight_count! > 0) && (
        <div className="px-4 py-3 bg-gradient-to-r from-gray-50 via-blue-50 to-purple-50 dark:from-gray-900 dark:via-gray-850 dark:to-gray-900 border-t-2 border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-4 text-xs text-gray-700 dark:text-gray-300">
            <span className="font-bold text-sm flex items-center gap-1">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              Legend:
            </span>
            <div className="flex items-center gap-1.5 px-2 py-1 bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-all duration-200">
              <span className="inline-block w-5 h-5 bg-gradient-to-r from-yellow-200 via-yellow-300 to-yellow-200 dark:from-yellow-800/70 dark:via-yellow-700/80 dark:to-yellow-800/70 rounded border-b-2 border-yellow-400 dark:border-yellow-600"></span>
              <span className="font-medium">Exact match</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-1 bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-all duration-200">
              <span className="inline-block w-5 h-5 bg-gradient-to-r from-blue-200 via-blue-300 to-blue-200 dark:from-blue-800/70 dark:via-blue-700/80 dark:to-blue-800/70 rounded border-b-2 border-blue-400 dark:border-blue-600"></span>
              <span className="font-medium">Fuzzy match</span>
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
        
        @keyframes pulse-subtle {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.85;
          }
        }
        
        :global(.animate-pulse-subtle) {
          animation: pulse-subtle 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        /* Shimmer effect for highlights */
        @keyframes shimmer {
          0% {
            background-position: -200% center;
          }
          100% {
            background-position: 200% center;
          }
        }
        
        :global(mark) {
          background-size: 200% 100%;
          animation: shimmer 3s ease-in-out infinite;
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
