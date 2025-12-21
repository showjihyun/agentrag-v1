'use client';

import React, { useMemo, useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { ImprovedFlowCard } from './ImprovedFlowCard';

interface VirtualizedFlowGridProps {
  flows: any[];
  type: 'agentflow' | 'chatflow';
  onAction: (action: string, flowId: string, flow?: any) => void;
  containerHeight?: number;
  containerWidth?: number;
}

export function VirtualizedFlowGrid({ 
  flows, 
  type, 
  onAction, 
  containerHeight = 600,
  containerWidth = 1200 
}: VirtualizedFlowGridProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  const { columnsPerRow, gridItems } = useMemo(() => {
    // 반응형 컬럼 계산
    const minCardWidth = 350;
    const gap = 24;
    const cols = Math.max(1, Math.floor((containerWidth + gap) / (minCardWidth + gap)));
    
    // 그리드 아이템들을 행별로 그룹화
    const items: any[][] = [];
    for (let i = 0; i < flows.length; i += cols) {
      items.push(flows.slice(i, i + cols));
    }
    
    return {
      columnsPerRow: cols,
      gridItems: items
    };
  }, [flows, containerWidth]);

  const rowVirtualizer = useVirtualizer({
    count: gridItems.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 304, // 카드 높이 280 + 패딩 24
    overscan: 2,
  });

  if (flows.length === 0) {
    return null;
  }

  return (
    <div
      ref={parentRef}
      style={{
        height: containerHeight,
        width: containerWidth,
        overflow: 'auto',
      }}
    >
      <div
        style={{
          height: rowVirtualizer.getTotalSize(),
          width: '100%',
          position: 'relative',
        }}
      >
        {rowVirtualizer.getVirtualItems().map((virtualRow) => {
          const rowFlows = gridItems[virtualRow.index];
          
          return (
            <div
              key={virtualRow.index}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: virtualRow.size,
                transform: `translateY(${virtualRow.start}px)`,
                display: 'grid',
                gridTemplateColumns: `repeat(${columnsPerRow}, 1fr)`,
                gap: '24px',
                padding: '12px',
              }}
            >
              {rowFlows.map((flow, colIndex) => (
                <ImprovedFlowCard
                  key={flow.id || `${virtualRow.index}-${colIndex}`}
                  flow={flow}
                  type={type}
                  onAction={onAction}
                />
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}