/**
 * Auto-layout algorithm for workflow nodes
 * Uses Dagre for hierarchical layout
 */

import { Node, Edge } from 'reactflow';

interface LayoutOptions {
  direction?: 'TB' | 'LR' | 'BT' | 'RL';
  nodeSpacing?: number;
  rankSpacing?: number;
}

/**
 * Apply automatic layout to nodes
 */
export function applyAutoLayout(
  nodes: Node[],
  edges: Edge[],
  options: LayoutOptions = {}
): Node[] {
  const {
    direction = 'TB',
    nodeSpacing = 100,
    rankSpacing = 150,
  } = options;

  // Build adjacency list
  const adjacency = new Map<string, string[]>();
  const inDegree = new Map<string, number>();

  nodes.forEach((node) => {
    adjacency.set(node.id, []);
    inDegree.set(node.id, 0);
  });

  edges.forEach((edge) => {
    adjacency.get(edge.source)?.push(edge.target);
    inDegree.set(edge.target, (inDegree.get(edge.target) || 0) + 1);
  });

  // Topological sort to determine layers
  const layers: string[][] = [];
  const queue: string[] = [];
  const visited = new Set<string>();

  // Find root nodes (no incoming edges)
  nodes.forEach((node) => {
    if (inDegree.get(node.id) === 0) {
      queue.push(node.id);
    }
  });

  while (queue.length > 0) {
    const currentLayer: string[] = [];
    const layerSize = queue.length;

    for (let i = 0; i < layerSize; i++) {
      const nodeId = queue.shift()!;
      currentLayer.push(nodeId);
      visited.add(nodeId);

      // Add children to queue
      adjacency.get(nodeId)?.forEach((childId) => {
        const degree = inDegree.get(childId)! - 1;
        inDegree.set(childId, degree);

        if (degree === 0 && !visited.has(childId)) {
          queue.push(childId);
        }
      });
    }

    if (currentLayer.length > 0) {
      layers.push(currentLayer);
    }
  }

  // Handle disconnected nodes
  nodes.forEach((node) => {
    if (!visited.has(node.id)) {
      layers.push([node.id]);
    }
  });

  // Calculate positions
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  const layoutedNodes: Node[] = [];

  layers.forEach((layer, layerIndex) => {
    const layerWidth = layer.length * nodeSpacing;
    const startX = -layerWidth / 2;

    layer.forEach((nodeId, nodeIndex) => {
      const node = nodeMap.get(nodeId);
      if (!node) return;

      let x: number, y: number;

      if (direction === 'TB' || direction === 'BT') {
        x = startX + nodeIndex * nodeSpacing;
        y = layerIndex * rankSpacing;
        if (direction === 'BT') y = -y;
      } else {
        x = layerIndex * rankSpacing;
        y = startX + nodeIndex * nodeSpacing;
        if (direction === 'RL') x = -x;
      }

      layoutedNodes.push({
        ...node,
        position: { x, y },
      });
    });
  });

  return layoutedNodes;
}

/**
 * Center nodes in viewport
 */
export function centerNodes(nodes: Node[]): Node[] {
  if (nodes.length === 0) return nodes;

  // Calculate bounds
  let minX = Infinity, minY = Infinity;
  let maxX = -Infinity, maxY = -Infinity;

  nodes.forEach((node) => {
    minX = Math.min(minX, node.position.x);
    minY = Math.min(minY, node.position.y);
    maxX = Math.max(maxX, node.position.x + (node.width || 200));
    maxY = Math.max(maxY, node.position.y + (node.height || 100));
  });

  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;

  // Center nodes
  return nodes.map((node) => ({
    ...node,
    position: {
      x: node.position.x - centerX,
      y: node.position.y - centerY,
    },
  }));
}

/**
 * Align nodes horizontally
 */
export function alignNodesHorizontally(nodes: Node[]): Node[] {
  if (nodes.length === 0) return nodes;

  const avgY = nodes.reduce((sum, n) => sum + n.position.y, 0) / nodes.length;

  return nodes.map((node) => ({
    ...node,
    position: {
      ...node.position,
      y: avgY,
    },
  }));
}

/**
 * Align nodes vertically
 */
export function alignNodesVertically(nodes: Node[]): Node[] {
  if (nodes.length === 0) return nodes;

  const avgX = nodes.reduce((sum, n) => sum + n.position.x, 0) / nodes.length;

  return nodes.map((node) => ({
    ...node,
    position: {
      ...node.position,
      x: avgX,
    },
  }));
}

/**
 * Distribute nodes evenly
 */
export function distributeNodesEvenly(
  nodes: Node[],
  direction: 'horizontal' | 'vertical',
  spacing: number = 100
): Node[] {
  if (nodes.length < 2) return nodes;

  const sorted = [...nodes].sort((a, b) => {
    return direction === 'horizontal'
      ? a.position.x - b.position.x
      : a.position.y - b.position.y;
  });

  return sorted.map((node, index) => ({
    ...node,
    position: {
      ...node.position,
      [direction === 'horizontal' ? 'x' : 'y']: index * spacing,
    },
  }));
}
