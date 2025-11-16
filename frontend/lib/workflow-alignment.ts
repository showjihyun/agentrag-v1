import { Node } from 'reactflow';

export interface AlignmentOptions {
  spacing?: number;
  padding?: number;
}

/**
 * Align nodes horizontally (same Y position)
 */
export function alignNodesHorizontal(nodes: Node[], options: AlignmentOptions = {}): Node[] {
  if (nodes.length < 2) return nodes;

  // Calculate average Y position
  const avgY = nodes.reduce((sum, node) => sum + node.position.y, 0) / nodes.length;

  return nodes.map(node => ({
    ...node,
    position: {
      ...node.position,
      y: avgY,
    },
  }));
}

/**
 * Align nodes vertically (same X position)
 */
export function alignNodesVertical(nodes: Node[], options: AlignmentOptions = {}): Node[] {
  if (nodes.length < 2) return nodes;

  // Calculate average X position
  const avgX = nodes.reduce((sum, node) => sum + node.position.x, 0) / nodes.length;

  return nodes.map(node => ({
    ...node,
    position: {
      ...node.position,
      x: avgX,
    },
  }));
}

/**
 * Align nodes to the left (minimum X)
 */
export function alignNodesLeft(nodes: Node[]): Node[] {
  if (nodes.length < 2) return nodes;

  const minX = Math.min(...nodes.map(node => node.position.x));

  return nodes.map(node => ({
    ...node,
    position: {
      ...node.position,
      x: minX,
    },
  }));
}

/**
 * Align nodes to the right (maximum X)
 */
export function alignNodesRight(nodes: Node[]): Node[] {
  if (nodes.length < 2) return nodes;

  const maxX = Math.max(...nodes.map(node => node.position.x));

  return nodes.map(node => ({
    ...node,
    position: {
      ...node.position,
      x: maxX,
    },
  }));
}

/**
 * Align nodes to the top (minimum Y)
 */
export function alignNodesTop(nodes: Node[]): Node[] {
  if (nodes.length < 2) return nodes;

  const minY = Math.min(...nodes.map(node => node.position.y));

  return nodes.map(node => ({
    ...node,
    position: {
      ...node.position,
      y: minY,
    },
  }));
}

/**
 * Align nodes to the bottom (maximum Y)
 */
export function alignNodesBottom(nodes: Node[]): Node[] {
  if (nodes.length < 2) return nodes;

  const maxY = Math.max(...nodes.map(node => node.position.y));

  return nodes.map(node => ({
    ...node,
    position: {
      ...node.position,
      y: maxY,
    },
  }));
}

/**
 * Distribute nodes horizontally with equal spacing
 */
export function distributeNodesHorizontal(nodes: Node[], options: AlignmentOptions = {}): Node[] {
  if (nodes.length < 3) return nodes;

  const { spacing = 50 } = options;

  // Sort by X position
  const sorted = [...nodes].sort((a, b) => a.position.x - b.position.x);

  // Calculate total width needed
  const minX = sorted[0].position.x;
  const maxX = sorted[sorted.length - 1].position.x;
  const totalWidth = maxX - minX;
  const gap = totalWidth / (sorted.length - 1);

  return sorted.map((node, index) => ({
    ...node,
    position: {
      ...node.position,
      x: minX + (gap * index),
    },
  }));
}

/**
 * Distribute nodes vertically with equal spacing
 */
export function distributeNodesVertical(nodes: Node[], options: AlignmentOptions = {}): Node[] {
  if (nodes.length < 3) return nodes;

  const { spacing = 50 } = options;

  // Sort by Y position
  const sorted = [...nodes].sort((a, b) => a.position.y - b.position.y);

  // Calculate total height needed
  const minY = sorted[0].position.y;
  const maxY = sorted[sorted.length - 1].position.y;
  const totalHeight = maxY - minY;
  const gap = totalHeight / (sorted.length - 1);

  return sorted.map((node, index) => ({
    ...node,
    position: {
      ...node.position,
      y: minY + (gap * index),
    },
  }));
}

/**
 * Get bounding box of nodes
 */
export function getNodesBounds(nodes: Node[]) {
  if (nodes.length === 0) {
    return { x: 0, y: 0, width: 0, height: 0 };
  }

  const xs = nodes.map(n => n.position.x);
  const ys = nodes.map(n => n.position.y);

  // Assume default node size if not specified
  const nodeWidth = 200;
  const nodeHeight = 100;

  const minX = Math.min(...xs);
  const minY = Math.min(...ys);
  const maxX = Math.max(...xs.map((x, i) => x + (nodes[i].width || nodeWidth)));
  const maxY = Math.max(...ys.map((y, i) => y + (nodes[i].height || nodeHeight)));

  return {
    x: minX,
    y: minY,
    width: maxX - minX,
    height: maxY - minY,
  };
}
