/**
 * Workflow Actions Hook
 * Provides context menu actions and node alignment utilities
 */

import { useCallback, useState } from 'react';
import { Node, Edge, useReactFlow } from 'reactflow';
import { useToast } from '@/hooks/use-toast';
import {
  alignNodesHorizontal,
  alignNodesVertical,
  alignNodesLeft,
  alignNodesRight,
  alignNodesTop,
  alignNodesBottom,
  distributeNodesHorizontal,
  distributeNodesVertical,
} from '@/lib/workflow-alignment';

export function useWorkflowActions() {
  const { toast } = useToast();
  const reactFlowInstance = useReactFlow();
  const [clipboard, setClipboard] = useState<{ nodes: Node[]; edges: Edge[] } | null>(null);

  // Copy selected nodes
  const copyNodes = useCallback(() => {
    const selectedNodes = reactFlowInstance.getNodes().filter(n => n.selected);
    const selectedNodeIds = selectedNodes.map(n => n.id);
    const selectedEdges = reactFlowInstance.getEdges().filter(
      e => selectedNodeIds.includes(e.source) && selectedNodeIds.includes(e.target)
    );

    if (selectedNodes.length === 0) {
      toast({
        title: 'No nodes selected',
        description: 'Select nodes to copy',
        variant: 'default',
      });
      return;
    }

    setClipboard({ nodes: selectedNodes, edges: selectedEdges });
    toast({
      title: 'Copied',
      description: `${selectedNodes.length} node(s) copied`,
    });
  }, [reactFlowInstance, toast]);

  // Paste nodes
  const pasteNodes = useCallback(() => {
    if (!clipboard) {
      toast({
        title: 'Nothing to paste',
        description: 'Copy nodes first',
        variant: 'default',
      });
      return;
    }

    const { nodes: copiedNodes, edges: copiedEdges } = clipboard;
    const idMap = new Map<string, string>();

    // Create new nodes with new IDs and offset positions
    const newNodes = copiedNodes.map(node => {
      const newId = `${node.type}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      idMap.set(node.id, newId);

      return {
        ...node,
        id: newId,
        position: {
          x: node.position.x + 50,
          y: node.position.y + 50,
        },
        selected: true,
      };
    });

    // Create new edges with updated IDs
    const newEdges = copiedEdges.map(edge => ({
      ...edge,
      id: `edge-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      source: idMap.get(edge.source) || edge.source,
      target: idMap.get(edge.target) || edge.target,
    }));

    // Deselect existing nodes
    const existingNodes = reactFlowInstance.getNodes().map(n => ({ ...n, selected: false }));

    reactFlowInstance.setNodes([...existingNodes, ...newNodes]);
    reactFlowInstance.setEdges([...reactFlowInstance.getEdges(), ...newEdges]);

    toast({
      title: 'Pasted',
      description: `${newNodes.length} node(s) pasted`,
    });
  }, [clipboard, reactFlowInstance, toast]);

  // Duplicate selected nodes
  const duplicateNodes = useCallback(() => {
    copyNodes();
    setTimeout(() => pasteNodes(), 100);
  }, [copyNodes, pasteNodes]);

  // Delete selected nodes
  const deleteNodes = useCallback(() => {
    const selectedNodes = reactFlowInstance.getNodes().filter(n => n.selected);
    
    if (selectedNodes.length === 0) {
      toast({
        title: 'No nodes selected',
        description: 'Select nodes to delete',
        variant: 'default',
      });
      return;
    }

    const selectedNodeIds = selectedNodes.map(n => n.id);
    
    reactFlowInstance.setNodes(nodes => nodes.filter(n => !selectedNodeIds.includes(n.id)));
    reactFlowInstance.setEdges(edges => edges.filter(
      e => !selectedNodeIds.includes(e.source) && !selectedNodeIds.includes(e.target)
    ));

    toast({
      title: 'Deleted',
      description: `${selectedNodes.length} node(s) deleted`,
    });
  }, [reactFlowInstance, toast]);

  // Align nodes horizontally
  const alignHorizontal = useCallback(() => {
    const selectedNodes = reactFlowInstance.getNodes().filter(n => n.selected);
    
    if (selectedNodes.length < 2) {
      toast({
        title: 'Select multiple nodes',
        description: 'Select at least 2 nodes to align',
        variant: 'default',
      });
      return;
    }

    const alignedNodes = alignNodesHorizontal(selectedNodes);
    const allNodes = reactFlowInstance.getNodes().map(node => {
      const aligned = alignedNodes.find(n => n.id === node.id);
      return aligned || node;
    });

    reactFlowInstance.setNodes(allNodes);
    
    toast({
      title: 'Aligned',
      description: `${selectedNodes.length} nodes aligned horizontally`,
    });
  }, [reactFlowInstance, toast]);

  // Align nodes vertically
  const alignVertical = useCallback(() => {
    const selectedNodes = reactFlowInstance.getNodes().filter(n => n.selected);
    
    if (selectedNodes.length < 2) {
      toast({
        title: 'Select multiple nodes',
        description: 'Select at least 2 nodes to align',
        variant: 'default',
      });
      return;
    }

    const alignedNodes = alignNodesVertical(selectedNodes);
    const allNodes = reactFlowInstance.getNodes().map(node => {
      const aligned = alignedNodes.find(n => n.id === node.id);
      return aligned || node;
    });

    reactFlowInstance.setNodes(allNodes);
    
    toast({
      title: 'Aligned',
      description: `${selectedNodes.length} nodes aligned vertically`,
    });
  }, [reactFlowInstance, toast]);

  // Align nodes to left
  const alignLeft = useCallback(() => {
    const selectedNodes = reactFlowInstance.getNodes().filter(n => n.selected);
    if (selectedNodes.length < 2) return;

    const alignedNodes = alignNodesLeft(selectedNodes);
    const allNodes = reactFlowInstance.getNodes().map(node => {
      const aligned = alignedNodes.find(n => n.id === node.id);
      return aligned || node;
    });

    reactFlowInstance.setNodes(allNodes);
  }, [reactFlowInstance]);

  // Align nodes to right
  const alignRight = useCallback(() => {
    const selectedNodes = reactFlowInstance.getNodes().filter(n => n.selected);
    if (selectedNodes.length < 2) return;

    const alignedNodes = alignNodesRight(selectedNodes);
    const allNodes = reactFlowInstance.getNodes().map(node => {
      const aligned = alignedNodes.find(n => n.id === node.id);
      return aligned || node;
    });

    reactFlowInstance.setNodes(allNodes);
  }, [reactFlowInstance]);

  // Distribute nodes horizontally
  const distributeHorizontal = useCallback(() => {
    const selectedNodes = reactFlowInstance.getNodes().filter(n => n.selected);
    if (selectedNodes.length < 3) {
      toast({
        title: 'Select more nodes',
        description: 'Select at least 3 nodes to distribute',
        variant: 'default',
      });
      return;
    }

    const distributedNodes = distributeNodesHorizontal(selectedNodes);
    const allNodes = reactFlowInstance.getNodes().map(node => {
      const distributed = distributedNodes.find(n => n.id === node.id);
      return distributed || node;
    });

    reactFlowInstance.setNodes(allNodes);
    
    toast({
      title: 'Distributed',
      description: `${selectedNodes.length} nodes distributed horizontally`,
    });
  }, [reactFlowInstance, toast]);

  // Distribute nodes vertically
  const distributeVertical = useCallback(() => {
    const selectedNodes = reactFlowInstance.getNodes().filter(n => n.selected);
    if (selectedNodes.length < 3) {
      toast({
        title: 'Select more nodes',
        description: 'Select at least 3 nodes to distribute',
        variant: 'default',
      });
      return;
    }

    const distributedNodes = distributeNodesVertical(selectedNodes);
    const allNodes = reactFlowInstance.getNodes().map(node => {
      const distributed = distributedNodes.find(n => n.id === node.id);
      return distributed || node;
    });

    reactFlowInstance.setNodes(allNodes);
    
    toast({
      title: 'Distributed',
      description: `${selectedNodes.length} nodes distributed vertically`,
    });
  }, [reactFlowInstance, toast]);

  // Group nodes
  const groupNodes = useCallback(() => {
    const selectedNodes = reactFlowInstance.getNodes().filter(n => n.selected);
    
    if (selectedNodes.length < 2) {
      toast({
        title: 'Select multiple nodes',
        description: 'Select at least 2 nodes to group',
        variant: 'default',
      });
      return;
    }

    // Calculate bounding box
    const xs = selectedNodes.map(n => n.position.x);
    const ys = selectedNodes.map(n => n.position.y);
    const minX = Math.min(...xs);
    const minY = Math.min(...ys);
    const maxX = Math.max(...xs.map((x, i) => x + (selectedNodes[i].width || 200)));
    const maxY = Math.max(...ys.map((y, i) => y + (selectedNodes[i].height || 100)));

    const padding = 20;
    const groupNode = {
      id: `group-${Date.now()}`,
      type: 'group',
      position: {
        x: minX - padding,
        y: minY - padding - 30, // Extra space for header
      },
      style: {
        width: maxX - minX + padding * 2,
        height: maxY - minY + padding * 2 + 30,
      },
      data: {
        label: 'New Group',
        color: 'Blue',
      },
    };

    // Deselect nodes and add group
    const updatedNodes = reactFlowInstance.getNodes().map(n => ({
      ...n,
      selected: false,
    }));

    reactFlowInstance.setNodes([...updatedNodes, groupNode]);

    toast({
      title: 'Group Created',
      description: `${selectedNodes.length} nodes grouped`,
    });
  }, [reactFlowInstance, toast]);

  // Add note
  const addNote = useCallback((position?: { x: number; y: number }) => {
    const notePosition = position || {
      x: 100,
      y: 100,
    };

    const noteNode = {
      id: `comment-${Date.now()}`,
      type: 'comment',
      position: notePosition,
      data: {
        text: '',
        color: 'Yellow',
        width: 250,
        height: 150,
      },
    };

    reactFlowInstance.setNodes([...reactFlowInstance.getNodes(), noteNode]);

    toast({
      title: 'Note Added',
      description: 'Click to edit the note',
    });
  }, [reactFlowInstance, toast]);

  // Auto layout
  const applyAutoLayout = useCallback((preset: 'horizontal' | 'vertical' | 'compact' | 'spacious') => {
    const { autoLayout, layoutPresets } = require('@/lib/workflow-layout');
    
    const nodes = reactFlowInstance.getNodes();
    const edges = reactFlowInstance.getEdges();

    if (nodes.length === 0) {
      toast({
        title: 'No nodes',
        description: 'Add nodes to apply layout',
        variant: 'default',
      });
      return;
    }

    const layoutedNodes = layoutPresets[preset].apply(nodes, edges);
    reactFlowInstance.setNodes(layoutedNodes);

    toast({
      title: 'Layout Applied',
      description: `${layoutPresets[preset].name} layout applied to ${nodes.length} nodes`,
    });
  }, [reactFlowInstance, toast]);

  // Select all nodes
  const selectAll = useCallback(() => {
    const allNodes = reactFlowInstance.getNodes().map(n => ({ ...n, selected: true }));
    reactFlowInstance.setNodes(allNodes);
    
    toast({
      title: 'Selected All',
      description: `${allNodes.length} nodes selected`,
    });
  }, [reactFlowInstance, toast]);

  // Fit view
  const fitView = useCallback(() => {
    reactFlowInstance.fitView({ padding: 0.2, duration: 300 });
  }, [reactFlowInstance]);

  return {
    // Clipboard actions
    copyNodes,
    pasteNodes,
    duplicateNodes,
    deleteNodes,
    hasClipboard: !!clipboard,
    
    // Alignment actions
    alignHorizontal,
    alignVertical,
    alignLeft,
    alignRight,
    distributeHorizontal,
    distributeVertical,
    
    // Layout actions
    applyAutoLayout,
    
    // Other actions
    groupNodes,
    addNote,
    selectAll,
    fitView,
  };
}
