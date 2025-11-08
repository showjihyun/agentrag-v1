/**
 * Virtual Scrolling Hook
 * 
 * Optimizes rendering of large lists by only rendering visible items
 */

import { useState, useEffect, useRef, useMemo, useCallback } from 'react';

interface UseVirtualScrollOptions {
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
  items: any[];
}

interface VirtualScrollResult {
  virtualItems: Array<{
    index: number;
    start: number;
    end: number;
    item: any;
  }>;
  totalHeight: number;
  scrollToIndex: (index: number) => void;
  containerRef: React.RefObject<HTMLDivElement>;
}

export const useVirtualScroll = ({
  itemHeight,
  containerHeight,
  overscan = 3,
  items,
}: UseVirtualScrollOptions): VirtualScrollResult => {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  // Calculate total height
  const totalHeight = useMemo(() => {
    return items.length * itemHeight;
  }, [items.length, itemHeight]);

  // Calculate visible range
  const { startIndex, endIndex } = useMemo(() => {
    const start = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const visibleCount = Math.ceil(containerHeight / itemHeight);
    const end = Math.min(items.length - 1, start + visibleCount + overscan * 2);
    
    return { startIndex: start, endIndex: end };
  }, [scrollTop, itemHeight, containerHeight, overscan, items.length]);

  // Create virtual items
  const virtualItems = useMemo(() => {
    const result = [];
    for (let i = startIndex; i <= endIndex; i++) {
      result.push({
        index: i,
        start: i * itemHeight,
        end: (i + 1) * itemHeight,
        item: items[i],
      });
    }
    return result;
  }, [startIndex, endIndex, itemHeight, items]);

  // Handle scroll
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      setScrollTop(container.scrollTop);
    };

    container.addEventListener('scroll', handleScroll, { passive: true });
    return () => container.removeEventListener('scroll', handleScroll);
  }, []);

  // Scroll to index
  const scrollToIndex = useCallback((index: number) => {
    const container = containerRef.current;
    if (!container) return;

    const targetScrollTop = index * itemHeight;
    container.scrollTo({
      top: targetScrollTop,
      behavior: 'smooth',
    });
  }, [itemHeight]);

  return {
    virtualItems,
    totalHeight,
    scrollToIndex,
    containerRef,
  };
};

/**
 * Advanced virtual scroll with dynamic heights
 */
interface UseAdvancedVirtualScrollOptions {
  estimatedItemHeight: number;
  containerHeight: number;
  overscan?: number;
  items: any[];
  getItemHeight?: (index: number) => number;
}

export const useAdvancedVirtualScroll = ({
  estimatedItemHeight,
  containerHeight,
  overscan = 3,
  items,
  getItemHeight,
}: UseAdvancedVirtualScrollOptions) => {
  const [scrollTop, setScrollTop] = useState(0);
  const [measuredHeights, setMeasuredHeights] = useState<Map<number, number>>(new Map());
  const containerRef = useRef<HTMLDivElement>(null);
  const itemRefs = useRef<Map<number, HTMLElement>>(new Map());

  // Measure item heights
  useEffect(() => {
    const newHeights = new Map(measuredHeights);
    let hasChanges = false;

    itemRefs.current.forEach((element, index) => {
      const height = element.getBoundingClientRect().height;
      if (measuredHeights.get(index) !== height) {
        newHeights.set(index, height);
        hasChanges = true;
      }
    });

    if (hasChanges) {
      setMeasuredHeights(newHeights);
    }
  }, [items]);

  // Calculate positions
  const itemPositions = useMemo(() => {
    const positions: Array<{ start: number; end: number; height: number }> = [];
    let currentPosition = 0;

    for (let i = 0; i < items.length; i++) {
      const height = getItemHeight?.(i) || measuredHeights.get(i) || estimatedItemHeight;
      positions.push({
        start: currentPosition,
        end: currentPosition + height,
        height,
      });
      currentPosition += height;
    }

    return positions;
  }, [items.length, measuredHeights, estimatedItemHeight, getItemHeight]);

  // Calculate visible range
  const { startIndex, endIndex } = useMemo(() => {
    let start = 0;
    let end = items.length - 1;

    // Binary search for start
    let left = 0;
    let right = items.length - 1;
    while (left <= right) {
      const mid = Math.floor((left + right) / 2);
      const position = itemPositions[mid];
      if (position.end < scrollTop) {
        left = mid + 1;
      } else {
        start = mid;
        right = mid - 1;
      }
    }

    // Find end
    const viewportEnd = scrollTop + containerHeight;
    for (let i = start; i < items.length; i++) {
      if (itemPositions[i].start > viewportEnd) {
        end = i;
        break;
      }
    }

    return {
      startIndex: Math.max(0, start - overscan),
      endIndex: Math.min(items.length - 1, end + overscan),
    };
  }, [scrollTop, containerHeight, itemPositions, items.length, overscan]);

  // Create virtual items
  const virtualItems = useMemo(() => {
    const result = [];
    for (let i = startIndex; i <= endIndex; i++) {
      const position = itemPositions[i];
      result.push({
        index: i,
        start: position.start,
        end: position.end,
        height: position.height,
        item: items[i],
      });
    }
    return result;
  }, [startIndex, endIndex, itemPositions, items]);

  // Total height
  const totalHeight = useMemo(() => {
    if (itemPositions.length === 0) return 0;
    return itemPositions[itemPositions.length - 1].end;
  }, [itemPositions]);

  // Handle scroll
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      setScrollTop(container.scrollTop);
    };

    container.addEventListener('scroll', handleScroll, { passive: true });
    return () => container.removeEventListener('scroll', handleScroll);
  }, []);

  // Scroll to index
  const scrollToIndex = useCallback((index: number) => {
    const container = containerRef.current;
    if (!container || !itemPositions[index]) return;

    const targetScrollTop = itemPositions[index].start;
    container.scrollTo({
      top: targetScrollTop,
      behavior: 'smooth',
    });
  }, [itemPositions]);

  // Register item ref
  const registerItemRef = useCallback((index: number, element: HTMLElement | null) => {
    if (element) {
      itemRefs.current.set(index, element);
    } else {
      itemRefs.current.delete(index);
    }
  }, []);

  return {
    virtualItems,
    totalHeight,
    scrollToIndex,
    containerRef,
    registerItemRef,
  };
};
