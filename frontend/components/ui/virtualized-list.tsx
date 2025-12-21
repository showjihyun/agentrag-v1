'use client';

import React, { forwardRef, useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { cn } from '@/lib/utils';

interface VirtualizedListProps<T> {
  items: T[];
  height: number;
  itemSize: number;
  renderItem: (props: { index: number; item: T }) => React.ReactElement;
  className?: string;
  overscanCount?: number;
}

interface VirtualizedListRef {
  scrollToIndex: (index: number, options?: { align?: 'start' | 'center' | 'end' | 'auto' }) => void;
}

function VirtualizedListInner<T>(
  { items, height, itemSize, renderItem, className, overscanCount = 5 }: VirtualizedListProps<T>,
  ref: React.Ref<VirtualizedListRef>
) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => itemSize,
    overscan: overscanCount,
  });

  React.useImperativeHandle(ref, () => ({
    scrollToIndex: (index: number, options?: { align?: 'start' | 'center' | 'end' | 'auto' }) => {
      virtualizer.scrollToIndex(index, options);
    },
  }));

  return (
    <div
      ref={parentRef}
      className={cn('scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100', className)}
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
          const item = items[virtualItem.index];
          
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
              {renderItem({ index: virtualItem.index, item })}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export const VirtualizedList = forwardRef(VirtualizedListInner) as <T>(
  props: VirtualizedListProps<T> & { ref?: React.Ref<VirtualizedListRef> }
) => React.ReactElement;