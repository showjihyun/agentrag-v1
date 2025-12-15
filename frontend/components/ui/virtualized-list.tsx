'use client';

import React, { forwardRef } from 'react';
import { FixedSizeList as List, ListChildComponentProps } from 'react-window';
import { cn } from '@/lib/utils';

interface VirtualizedListProps<T> {
  items: T[];
  height: number;
  itemSize: number;
  renderItem: (props: ListChildComponentProps & { item: T }) => React.ReactElement;
  className?: string;
  overscanCount?: number;
}

function VirtualizedListInner<T>(
  { items, height, itemSize, renderItem, className, overscanCount = 5 }: VirtualizedListProps<T>,
  ref: React.Ref<List>
) {
  const ItemRenderer = ({ index, style }: ListChildComponentProps) => {
    const item = items[index];
    return renderItem({ index, style, item });
  };

  return (
    <List
      ref={ref}
      className={cn('scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100', className)}
      height={height}
      itemCount={items.length}
      itemSize={itemSize}
      overscanCount={overscanCount}
    >
      {ItemRenderer}
    </List>
  );
}

export const VirtualizedList = forwardRef(VirtualizedListInner) as <T>(
  props: VirtualizedListProps<T> & { ref?: React.Ref<List> }
) => React.ReactElement;