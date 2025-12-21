/**
 * Virtual Message List Component
 * 
 * Optimized message list using @tanstack/react-virtual for virtual scrolling
 * Handles 1000+ messages with 60fps performance
 */

'use client';

import React, { memo, useRef, useEffect } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Message } from './MessageList';
import MessageItem from './MessageItem';

interface VirtualMessageListProps {
  messages: Message[];
  onReply?: (messageId: string) => void;
  onCopy?: (content: string) => void;
  itemHeight?: number;
  height?: number;
}

export const VirtualMessageList = memo<VirtualMessageListProps>(({
  messages,
  onReply,
  onCopy,
  itemHeight = 150,
  height = 400,
}) => {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => itemHeight,
    overscan: 5,
  });

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (messages.length > 0) {
      virtualizer.scrollToIndex(messages.length - 1, { align: 'end' });
    }
  }, [messages.length, virtualizer]);

  // Empty state
  if (messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        <p>No messages yet. Start a conversation!</p>
      </div>
    );
  }

  return (
    <div
      ref={parentRef}
      style={{
        height,
        overflow: 'auto',
      }}
    >
      <div
        style={{
          height: virtualizer.getTotalSize(),
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => {
          const message = messages[virtualItem.index];
          
          return (
            <div
              key={virtualItem.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: virtualItem.size,
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              <MessageItem
                message={message}
                onReply={onReply}
                onCopy={onCopy}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
});

VirtualMessageList.displayName = 'VirtualMessageList';
