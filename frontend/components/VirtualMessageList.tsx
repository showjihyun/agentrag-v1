/**
 * Virtual Message List Component
 * 
 * Optimized message list using react-window for virtual scrolling
 * Handles 1000+ messages with 60fps performance
 */

'use client';

import React, { memo, useRef, useEffect } from 'react';
import { FixedSizeList as List, ListChildComponentProps } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';
import { Message } from './MessageList';
import MessageItem from './MessageItem';

interface VirtualMessageListProps {
  messages: Message[];
  onReply?: (messageId: string) => void;
  onCopy?: (content: string) => void;
  itemHeight?: number;
}

// Memoized row component
const Row = memo(({ index, style, data }: ListChildComponentProps<{
  messages: Message[];
  onReply?: (messageId: string) => void;
  onCopy?: (content: string) => void;
}>) => {
  const { messages, onReply, onCopy } = data;
  const message = messages[index];

  return (
    <div style={style}>
      <MessageItem
        message={message}
        onReply={onReply}
        onCopy={onCopy}
      />
    </div>
  );
});

Row.displayName = 'VirtualMessageRow';

export const VirtualMessageList = memo<VirtualMessageListProps>(({
  messages,
  onReply,
  onCopy,
  itemHeight = 150,
}) => {
  const listRef = useRef<List>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (listRef.current && messages.length > 0) {
      listRef.current.scrollToItem(messages.length - 1, 'end');
    }
  }, [messages.length]);

  // Empty state
  if (messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        <p>No messages yet. Start a conversation!</p>
      </div>
    );
  }

  return (
    <AutoSizer>
      {({ height, width }) => (
        <List
          ref={listRef}
          height={height}
          width={width}
          itemCount={messages.length}
          itemSize={itemHeight}
          itemData={{ messages, onReply, onCopy }}
          overscanCount={5}
        >
          {Row}
        </List>
      )}
    </AutoSizer>
  );
});

VirtualMessageList.displayName = 'VirtualMessageList';
