import { useState, useCallback } from 'react';
import { Node } from 'reactflow';

interface UseClipboardReturn {
  copiedNodes: Node[];
  copy: (nodes: Node[]) => void;
  paste: (offsetX?: number, offsetY?: number) => Node[];
  clear: () => void;
}

/**
 * Hook for managing clipboard operations (copy/paste nodes)
 */
export function useClipboard(): UseClipboardReturn {
  const [copiedNodes, setCopiedNodes] = useState<Node[]>([]);

  const copy = useCallback((nodes: Node[]) => {
    // Deep clone nodes to avoid reference issues
    const clonedNodes = nodes.map((node) => ({
      ...node,
      data: { ...node.data },
    }));
    setCopiedNodes(clonedNodes);
  }, []);

  const paste = useCallback(
    (offsetX: number = 50, offsetY: number = 50): Node[] => {
      if (copiedNodes.length === 0) return [];

      // Create new nodes with offset positions and new IDs
      const pastedNodes = copiedNodes.map((node) => ({
        ...node,
        id: `${node.id}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        position: {
          x: node.position.x + offsetX,
          y: node.position.y + offsetY,
        },
        data: {
          ...node.data,
          status: 'idle', // Reset status
          executionTime: undefined,
        },
        selected: true, // Select pasted nodes
      }));

      return pastedNodes;
    },
    [copiedNodes]
  );

  const clear = useCallback(() => {
    setCopiedNodes([]);
  }, []);

  return {
    copiedNodes,
    copy,
    paste,
    clear,
  };
}
