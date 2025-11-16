/**
 * Workflow Performance Utilities
 * Memoization and optimization helpers
 */

import { Node, Edge } from 'reactflow';
import { memo } from 'react';

/**
 * Compare function for React.memo
 * Only re-render if these props change
 */
export function nodePropsAreEqual(
  prevProps: any,
  nextProps: any
): boolean {
  // Always re-render if selected state changes
  if (prevProps.selected !== nextProps.selected) {
    return false;
  }

  // Re-render if data changes
  if (JSON.stringify(prevProps.data) !== JSON.stringify(nextProps.data)) {
    return false;
  }

  // Re-render if dragging state changes
  if (prevProps.dragging !== nextProps.dragging) {
    return false;
  }

  // Re-render if position changes significantly (> 1px)
  if (
    Math.abs(prevProps.xPos - nextProps.xPos) > 1 ||
    Math.abs(prevProps.yPos - nextProps.yPos) > 1
  ) {
    return false;
  }

  // Don't re-render otherwise
  return true;
}

/**
 * Memoize node component
 */
export function memoizeNode<T>(Component: React.ComponentType<T>) {
  return memo(Component, nodePropsAreEqual as any);
}

/**
 * Debounce function for expensive operations
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null;
      func(...args);
    };

    if (timeout) {
      clearTimeout(timeout);
    }
    timeout = setTimeout(later, wait);
  };
}

/**
 * Throttle function for frequent events
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;

  return function executedFunction(...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * Calculate if nodes are in viewport
 * For virtual rendering optimization
 */
export function getNodesInViewport(
  nodes: Node[],
  viewport: { x: number; y: number; zoom: number },
  viewportWidth: number,
  viewportHeight: number
): Node[] {
  const { x, y, zoom } = viewport;

  // Calculate visible area
  const visibleLeft = -x / zoom;
  const visibleTop = -y / zoom;
  const visibleRight = visibleLeft + viewportWidth / zoom;
  const visibleBottom = visibleTop + viewportHeight / zoom;

  // Add padding for smooth scrolling
  const padding = 200;

  return nodes.filter((node) => {
    const nodeRight = node.position.x + (node.width || 200);
    const nodeBottom = node.position.y + (node.height || 100);

    return (
      nodeRight > visibleLeft - padding &&
      node.position.x < visibleRight + padding &&
      nodeBottom > visibleTop - padding &&
      node.position.y < visibleBottom + padding
    );
  });
}

/**
 * Batch node updates for better performance
 */
export class NodeUpdateBatcher {
  private updates: Map<string, Partial<Node>> = new Map();
  private timeout: NodeJS.Timeout | null = null;
  private callback: (updates: Map<string, Partial<Node>>) => void;

  constructor(callback: (updates: Map<string, Partial<Node>>) => void, delay: number = 16) {
    this.callback = callback;
  }

  add(nodeId: string, update: Partial<Node>) {
    this.updates.set(nodeId, {
      ...this.updates.get(nodeId),
      ...update,
    });

    if (this.timeout) {
      clearTimeout(this.timeout);
    }

    this.timeout = setTimeout(() => {
      this.flush();
    }, 16); // ~60fps
  }

  flush() {
    if (this.updates.size > 0) {
      this.callback(new Map(this.updates));
      this.updates.clear();
    }
  }
}

/**
 * Performance monitoring
 */
export class PerformanceMonitor {
  private metrics: Map<string, number[]> = new Map();

  measure(name: string, fn: () => void) {
    const start = performance.now();
    fn();
    const duration = performance.now() - start;

    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }

    const measurements = this.metrics.get(name)!;
    measurements.push(duration);

    // Keep only last 100 measurements
    if (measurements.length > 100) {
      measurements.shift();
    }
  }

  getStats(name: string) {
    const measurements = this.metrics.get(name) || [];
    if (measurements.length === 0) {
      return null;
    }

    const sum = measurements.reduce((a, b) => a + b, 0);
    const avg = sum / measurements.length;
    const max = Math.max(...measurements);
    const min = Math.min(...measurements);

    return { avg, max, min, count: measurements.length };
  }

  clear() {
    this.metrics.clear();
  }
}

/**
 * Optimize edge rendering
 */
export function shouldRenderEdge(
  edge: Edge,
  nodes: Node[],
  viewport: { x: number; y: number; zoom: number }
): boolean {
  // Always render if zoomed in
  if (viewport.zoom > 0.5) {
    return true;
  }

  // Find source and target nodes
  const sourceNode = nodes.find((n) => n.id === edge.source);
  const targetNode = nodes.find((n) => n.id === edge.target);

  if (!sourceNode || !targetNode) {
    return false;
  }

  // Calculate edge bounds
  const minX = Math.min(sourceNode.position.x, targetNode.position.x);
  const maxX = Math.max(
    sourceNode.position.x + (sourceNode.width || 200),
    targetNode.position.x + (targetNode.width || 200)
  );
  const minY = Math.min(sourceNode.position.y, targetNode.position.y);
  const maxY = Math.max(
    sourceNode.position.y + (sourceNode.height || 100),
    targetNode.position.y + (targetNode.height || 100)
  );

  // Check if edge is in viewport
  const { x, y, zoom } = viewport;
  const visibleLeft = -x / zoom;
  const visibleTop = -y / zoom;
  const visibleRight = visibleLeft + window.innerWidth / zoom;
  const visibleBottom = visibleTop + window.innerHeight / zoom;

  return (
    maxX > visibleLeft &&
    minX < visibleRight &&
    maxY > visibleTop &&
    minY < visibleBottom
  );
}
