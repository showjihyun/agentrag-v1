'use client';

import React, { useEffect, useRef } from 'react';
import { AgentStep, SearchResult } from '@/lib/types';
import ReasoningSteps from '@/components/ReasoningSteps';
import SourceCitations from '@/components/SourceCitations';
import ResponseStatusBadge from '@/components/ResponseStatusBadge';
import RefinementHighlight from '@/components/RefinementHighlight';
import ResponseComparison from '@/components/ResponseComparison';
import CacheIndicator from '@/components/CacheIndicator';
import ResponseFeedback from '@/components/ResponseFeedback';
import { EmptyState } from '@/components/ui/EmptyState';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  reasoningSteps?: AgentStep[];
  sources?: SearchResult[];
  // Progressive response properties
  responseType?: 'preliminary' | 'refinement' | 'final';
  pathSource?: 'speculative' | 'agentic' | 'hybrid';
  confidenceScore?: number;
  isRefining?: boolean;
  previousContent?: string; // For comparison toggle
  // Cache properties
  isCached?: boolean;
  cacheSimilarity?: number;
  cacheType?: 'exact' | 'semantic';
  // Performance metrics
  processingTime?: number; // Processing time in seconds
}

interface MessageListProps {
  messages: Message[];
  isProcessing?: boolean;
}

const MessageList: React.FC<MessageListProps> = ({ messages, isProcessing }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isUserScrolling, setIsUserScrolling] = React.useState(false);
  const [shouldAutoScroll, setShouldAutoScroll] = React.useState(true);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastScrollTop = useRef<number>(0);

  // Detect if user is scrolling
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
      
      // Check if user scrolled up
      const scrolledUp = scrollTop < lastScrollTop.current;
      lastScrollTop.current = scrollTop;

      if (scrolledUp && !isAtBottom) {
        setIsUserScrolling(true);
        setShouldAutoScroll(false);
      } else if (isAtBottom) {
        setIsUserScrolling(false);
        setShouldAutoScroll(true);
      }

      // Clear existing timeout
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }

      // Set timeout to reset scrolling state
      scrollTimeoutRef.current = setTimeout(() => {
        setIsUserScrolling(false);
      }, 1000);
    };

    container.addEventListener('scroll', handleScroll);
    return () => {
      container.removeEventListener('scroll', handleScroll);
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  // Auto-scroll with improved behavior
  useEffect(() => {
    if (shouldAutoScroll && !isUserScrolling) {
      // Use requestAnimationFrame for smoother scrolling
      requestAnimationFrame(() => {
        messagesEndRef.current?.scrollIntoView({ 
          behavior: 'smooth',
          block: 'end',
          inline: 'nearest'
        });
      });
    }
  }, [messages, shouldAutoScroll, isUserScrolling]);
  
  // Force scroll to bottom on new user message
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.role === 'user') {
        setShouldAutoScroll(true);
        setIsUserScrolling(false);
        requestAnimationFrame(() => {
          messagesEndRef.current?.scrollIntoView({ 
            behavior: 'smooth',
            block: 'end'
          });
        });
      }
    }
  }, [messages.length]);

  return (
    <div 
      ref={containerRef} 
      className="flex-1 overflow-y-auto p-4 relative"
      style={{ 
        minHeight: 0,
        scrollBehavior: 'smooth',
        overscrollBehavior: 'contain'
      }}
      role="log"
      aria-live="polite"
      aria-label="Chat messages"
    >
      {messages.length === 0 ? (
        <EmptyState
          icon={
            <svg className="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          }
          title="Start Your First Conversation"
          description="Ask questions about your documents and get intelligent answers powered by AI"
          examples={[
            "What are the main topics in my documents?",
            "Summarize the key points",
            "Find information about specific topics"
          ]}
        />
      ) : (
        <div className="space-y-6">
          {messages.map((message, index) => (
            <div
              key={message.id}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              } animate-fadeIn`}
              style={{
                animationDelay: `${index * 0.05}s`,
                animationFillMode: 'both'
              }}
              role="article"
              aria-label={`${message.role === 'user' ? 'User' : 'Assistant'} message`}
            >
              <div
                className={`w-full max-w-3xl ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-md hover:shadow-lg'
                } rounded-2xl p-5 transition-all duration-200`}
                style={{ minWidth: 0 }}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                      message.role === 'user'
                        ? 'bg-blue-700'
                        : 'bg-gray-200 dark:bg-gray-700'
                    }`}
                  >
                    {message.role === 'user' ? (
                      <svg
                        className="w-5 h-5"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : (
                      <svg
                        className="w-5 h-5 text-gray-600 dark:text-gray-300"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z" />
                        <path d="M15 7v2a4 4 0 01-4 4H9.828l-1.766 1.767c.28.149.599.233.938.233h2l3 3v-3h2a2 2 0 002-2V9a2 2 0 00-2-2h-1z" />
                      </svg>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium mb-1">
                      {message.role === 'user' ? 'You' : 'Assistant'}
                    </p>
                    
                    {message.role === 'assistant' && (
                      <div className="mb-2 flex flex-wrap items-center gap-2">
                        <ResponseStatusBadge
                          responseType={message.responseType}
                          pathSource={message.pathSource}
                          confidenceScore={message.confidenceScore}
                          isRefining={message.isRefining}
                        />
                        <CacheIndicator
                          isCached={message.isCached || false}
                          similarity={message.cacheSimilarity}
                          cacheType={message.cacheType}
                        />
                      </div>
                    )}
                    
                    {message.role === 'assistant' && message.responseType ? (
                      message.isRefining ? (
                        <RefinementHighlight
                          content={message.content}
                          previousContent={message.previousContent}
                          isRefining={message.isRefining}
                        />
                      ) : (
                        <ResponseComparison
                          currentContent={message.content}
                          previousContent={message.previousContent}
                          responseType={message.responseType}
                        />
                      )
                    ) : (
                      <div className="prose prose-sm dark:prose-invert max-w-none break-words overflow-wrap-anywhere">
                        <p className="whitespace-pre-wrap break-words">{message.content || ''}</p>
                      </div>
                    )}
                    {message.reasoningSteps && message.reasoningSteps.length > 0 && (
                      <div className="mt-3">
                        <ReasoningSteps 
                          steps={message.reasoningSteps} 
                          isProcessing={message.role === 'assistant' && message.isRefining}
                        />
                      </div>
                    )}
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3">
                        <SourceCitations sources={message.sources} />
                      </div>
                    )}
                    
                    {message.role === 'assistant' && message.responseType === 'final' && (
                      <ResponseFeedback
                        messageId={message.id}
                        onFeedback={async (rating, details) => {
                          // Send feedback to backend
                          try {
                            await fetch('/api/feedback', {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({
                                message_id: message.id,
                                rating,
                                details,
                                mode: message.pathSource,
                                confidence: message.confidenceScore,
                                timestamp: new Date().toISOString()
                              })
                            });
                          } catch (error) {
                            console.error('Failed to submit feedback:', error);
                          }
                        }}
                      />
                    )}
                    
                    <div className="flex items-center gap-3 text-xs opacity-70 mt-2">
                      <span>{message.timestamp.toLocaleTimeString()}</span>
                      {message.role === 'assistant' && message.processingTime !== undefined && (
                        <span className="flex items-center gap-1">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          {message.processingTime < 1 
                            ? `${(message.processingTime * 1000).toFixed(0)}ms`
                            : `${message.processingTime.toFixed(2)}s`
                          }
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
          {isProcessing && (
            <div className="flex justify-start animate-fadeIn">
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-5">
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                    <svg
                      className="w-5 h-5 text-white animate-spin"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                  </div>
                  <div className="flex flex-col">
                    <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      AI is thinking...
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      Analyzing your question
                    </div>
                  </div>
                  <div className="flex gap-1 ml-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      <div ref={messagesEndRef} className="h-4" />
      
      {/* Scroll to bottom button with badge */}
      {!shouldAutoScroll && (
        <button
          onClick={() => {
            setShouldAutoScroll(true);
            setIsUserScrolling(false);
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
          }}
          className="fixed bottom-32 right-8 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white rounded-full p-3 shadow-xl transition-all duration-300 hover:scale-110 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 z-20 animate-slideUp"
          aria-label="Scroll to bottom"
          title="New messages available"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
          {isProcessing && (
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
            </span>
          )}
        </button>
      )}
      
      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
        
        .animate-slideUp {
          animation: slideUp 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};

MessageList.displayName = 'MessageList';

export default React.memo(MessageList);
