'use client';

/**
 * Enhanced Virtual Message List
 * 
 * Optimized message list with virtual scrolling for better performance
 */

import React, { useCallback, useMemo } from 'react';
import { useAdvancedVirtualScroll } from '@/lib/hooks/useVirtualScroll';
import MessageItem, { Message } from '@/components/MessageItem';
import MessageSkeleton from '@/components/MessageSkeleton';
import { EmptyState } from '@/components/ui/EmptyState';

interface VirtualMessageListProps {
  messages: Message[];
  isProcessing?: boolean;
  onRegenerate?: (messageId: string) => void;
  onRelatedQuestionClick?: (question: string) => void;
  onChunkClick?: (chunkId: string) => void;
  containerHeight?: number;
}

const VirtualMessageList: React.FC<VirtualMessageListProps> = ({
  messages,
  isProcessing,
  onRegenerate,
  onRelatedQuestionClick,
  onChunkClick,
  containerHeight = 600,
}) => {
  // Memoize messages
  const memoizedMessages = useMemo(() => messages, [messages]);

  // Virtual scroll hook
  const {
    virtualItems,
    totalHeight,
    scrollToIndex,
    containerRef,
    registerItemRef,
  } = useAdvancedVirtualScroll({
    estimatedItemHeight: 200,
    containerHeight,
    overscan: 2,
    items: memoizedMessages,
  });

  // Scroll to bottom when new message arrives
  React.useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.role === 'user') {
        setTimeout(() => {
          scrollToIndex(messages.length - 1);
        }, 100);
      }
    }
  }, [messages.length, scrollToIndex]);

  // Memoized handlers
  const handleRegenerate = useCallback((messageId: string) => {
    onRegenerate?.(messageId);
  }, [onRegenerate]);

  const handleRelatedQuestionClick = useCallback((question: string) => {
    onRelatedQuestionClick?.(question);
  }, [onRelatedQuestionClick]);

  const handleChunkClick = useCallback((chunkId: string) => {
    onChunkClick?.(chunkId);
  }, [onChunkClick]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 overflow-y-auto p-4">
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
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className="flex-1 overflow-y-auto p-4 relative"
      style={{ 
        height: containerHeight,
        overscrollBehavior: 'contain'
      }}
      role="log"
      aria-live="polite"
      aria-label="Chat messages"
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        {virtualItems.map(({ index, start, item }) => (
          <div
            key={item.id}
            ref={(el) => registerItemRef(index, el)}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${start}px)`,
            }}
          >
            <MessageItem
              message={item}
              index={index}
              onRegenerate={handleRegenerate}
              onRelatedQuestionClick={handleRelatedQuestionClick}
              onChunkClick={handleChunkClick}
            />
          </div>
        ))}
        
        {isProcessing && (
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${totalHeight}px)`,
            }}
          >
            <MessageSkeleton />
          </div>
        )}
      </div>

      {/* Scroll to bottom button */}
      <button
        onClick={() => scrollToIndex(messages.length - 1)}
        className="fixed bottom-32 right-8 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white rounded-full p-3 shadow-xl transition-all duration-300 hover:scale-110 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 z-20"
        aria-label="Scroll to bottom"
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
    </div>
  );
};

VirtualMessageList.displayName = 'VirtualMessageList';

export default React.memo(VirtualMessageList);
