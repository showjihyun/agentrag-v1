import React, { memo } from 'react';
import { AgentStep, SearchResult } from '@/lib/types';
import ReasoningSteps from '@/components/ReasoningSteps';
import SourceCitations from '@/components/SourceCitations';
import ResponseStatusBadge from '@/components/ResponseStatusBadge';
import RefinementHighlight from '@/components/RefinementHighlight';
import ResponseComparison from '@/components/ResponseComparison';
import CacheIndicator from '@/components/CacheIndicator';
import ResponseFeedback from '@/components/ResponseFeedback';
import RegenerateButton from '@/components/RegenerateButton';
import RelatedQuestions from '@/components/RelatedQuestions';
import TypewriterText from '@/components/TypewriterText';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  reasoningSteps?: AgentStep[];
  sources?: SearchResult[];
  responseType?: 'preliminary' | 'refinement' | 'final';
  pathSource?: 'speculative' | 'agentic' | 'hybrid';
  confidenceScore?: number;
  isRefining?: boolean;
  previousContent?: string;
  isCached?: boolean;
  cacheSimilarity?: number;
  cacheType?: 'exact' | 'semantic';
  processingTime?: number;
}

interface MessageItemProps {
  message: Message;
  index: number;
  onRegenerate?: (messageId: string) => void;
  onRelatedQuestionClick?: (question: string) => void;
  onChunkClick?: (chunkId: string) => void;
}

const MessageItem: React.FC<MessageItemProps> = memo(({ message, index, onRegenerate, onRelatedQuestionClick, onChunkClick }) => {
  return (
    <div
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
                <p className="whitespace-pre-wrap break-words">
                  {message.role === 'assistant' && message.isRefining ? (
                    <TypewriterText text={message.content || ''} speed={20} />
                  ) : (
                    message.content || ''
                  )}
                </p>
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
                <SourceCitations sources={message.sources} onChunkClick={onChunkClick} />
              </div>
            )}
            
            {message.role === 'assistant' && message.responseType === 'final' && (
              <>
                <div className="mt-3 flex items-center gap-3 flex-wrap">
                  {onRegenerate && (
                    <RegenerateButton
                      onRegenerate={() => onRegenerate(message.id)}
                      isProcessing={false}
                      disabled={false}
                    />
                  )}
                  
                  <ResponseFeedback
                    messageId={message.id}
                    onFeedback={async (rating, details) => {
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
                </div>

                {onRelatedQuestionClick && (
                  <RelatedQuestions
                    currentQuery={message.content}
                    answer={message.content}
                    sources={message.sources}
                    onQuestionClick={onRelatedQuestionClick}
                    isProcessing={false}
                  />
                )}
              </>
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
  );
}, (prevProps, nextProps) => {
  // Custom comparison for better performance
  return (
    prevProps.message.id === nextProps.message.id &&
    prevProps.message.content === nextProps.message.content &&
    prevProps.message.isRefining === nextProps.message.isRefining &&
    prevProps.message.reasoningSteps?.length === nextProps.message.reasoningSteps?.length &&
    prevProps.message.sources?.length === nextProps.message.sources?.length
  );
});

MessageItem.displayName = 'MessageItem';

export default MessageItem;
