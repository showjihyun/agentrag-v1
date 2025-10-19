'use client';

import React, { useEffect, useRef, useMemo } from 'react';
import { EmptyState } from '@/components/ui/EmptyState';
import MessageItem, { Message } from '@/components/MessageItem';
import MessageSkeleton from '@/components/MessageSkeleton';

export type { Message };

interface MessageListProps {
  messages: Message[];
  isProcessing?: boolean;
  onRegenerate?: (messageId: string) => void;
  onRelatedQuestionClick?: (question: string) => void;
}

const MessageList: React.FC<MessageListProps> = ({ messages, isProcessing, onRegenerate, onRelatedQuestionClick }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isUserScrolling, setIsUserScrolling] = React.useState(false);
  const [shouldAutoScroll, setShouldAutoScroll] = React.useState(true);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastScrollTop = useRef<number>(0);
  
  // Memoize messages to prevent unnecessary re-renders
  const memoizedMessages = useMemo(() => messages, [messages]);

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
          {memoizedMessages.map((message, index) => (
            <MessageItem
              key={message.id}
              message={message}
              index={index}
              onRegenerate={onRegenerate}
              onRelatedQuestionClick={onRelatedQuestionClick}
            />
          ))}
          {isProcessing && <MessageSkeleton />}
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
