/**
 * Workflow Auto Layout
 * Uses Dagre for automatic graph layout
 */

import { Node, Edge } from 'reactflow';
import dagre from 'dagre';

export interface LayoutOptions {
  direction?: 'TB' | 'BT' | 'LR' | 'RL'; // Top-Bottom, Bottom-Top, Left-Right, Right-Left
  nodeWidth?: number;
  nodeHeight?: number;
  rankSep?: number; // Separation between ranks
  nodeSep?: number; // Separation between nodes in same rank
  edgeSep?: number; // Separation between edges
}

const defaultOptions: Required<LayoutOptions> = {
  direction: 'LR',
  nodeWidth: 200,
  nodeHeight: 100,
  rankSep: 100,
  nodeSep: 50,
  edgeSep: 10,
};

/**
 * Apply automatic layout to workflow nodes
 */
export function autoLayout(
  nodes: Node[],
  edges: Edge[],
  options: LayoutOptions = {}
): Node[] {
  const opts = { ...defaultOptions, ...options };

  // Create a new directed graph
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  // Set graph options
  dagreGraph.setGraph({
    rankdir: opts.direction,
    ranksep: opts.rankSep,
    nodesep: opts.nodeSep,
    edgesep: opts.edgeSep,
  });

  // Add nodes to the graph
  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, {
      width: node.width || opts.nodeWidth,
      height: node.height || opts.nodeHeight,
    });
  });

  // Add edges to the graph
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  // Calculate layout
  dagre.layout(dagreGraph);

  // Apply layout to nodes
  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);

    return {
      ...node,
      position: {
        // Dagre returns center position, we need top-left
        x: nodeWithPosition.x - (node.width || opts.nodeWidth) / 2,
        y: nodeWithPosition.y - (node.height || opts.nodeHeight) / 2,
      },
    };
  });

  return layoutedNodes;
}

/**
 * Layout nodes in a tree structure
 */
export function treeLayout(
  nodes: Node[],
  edges: Edge[],
  options: LayoutOptions = {}
): Node[] {
  return autoLayout(nodes, edges, { ...options, direction: 'TB' });
}

/**
 * Layout nodes horizontally (left to right)
 */
export function horizontalLayout(
  nodes: Node[],
  edges: Edge[],
  options: LayoutOptions = {}
): Node[] {
  return autoLayout(nodes, edges, { ...options, direction: 'LR' });
}

/**
 * Layout nodes vertically (top to bottom)
 */
export function verticalLayout(
  nodes: Node[],
  edges: Edge[],
  options: LayoutOptions = {}
): Node[] {
  return autoLayout(nodes, edges, { ...options, direction: 'TB' });
}

/**
 * Compact layout with minimal spacing
 */
export function compactLayout(
  nodes: Node[],
  edges: Edge[],
  options: LayoutOptions = {}
): Node[] {
  return autoLayout(nodes, edges, {
    ...options,
    rankSep: 60,
    nodeSep: 30,
    edgeSep: 5,
  });
}

/**
 * Spacious layout with more breathing room
 */
export function spaciousLayout(
  nodes: Node[],
  edges: Edge[],
  options: LayoutOptions = {}
): Node[] {
  return autoLayout(nodes, edges, {
    ...options,
    rankSep: 150,
    nodeSep: 80,
    edgeSep: 20,
  });
}

/**
 * Get layout presets
 */
export const layoutPresets = {
  horizontal: {
    name: 'Horizontal',
    description: 'Left to right flow',
    apply: horizontalLayout,
  },
  vertical: {
    name: 'Vertical',
    description: 'Top to bottom flow',
    apply: verticalLayout,
  },
  compact: {
    name: 'Compact',
    description: 'Minimal spacing',
    apply: compactLayout,
  },
  spacious: {
    name: 'Spacious',
    description: 'More breathing room',
    apply: spaciousLayout,
  },
} as const;

export type LayoutPreset = keyof typeof layoutPresets;
