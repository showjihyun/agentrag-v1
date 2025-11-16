'use client';

import React from 'react';
import { MiniMap, Node } from 'reactflow';

interface EnhancedMiniMapProps {
  className?: string;
}

/**
 * Enhanced MiniMap with better styling and node colors
 */
export function EnhancedMiniMap({ className }: EnhancedMiniMapProps) {
  // Node color based on type
  const nodeColor = (node: Node) => {
    // Execution status colors (if available)
    if (node.data?.executionStatus) {
      switch (node.data.executionStatus) {
        case 'running':
          return '#3b82f6'; // Blue
        case 'success':
          return '#10b981'; // Green
        case 'failed':
          return '#ef4444'; // Red
        case 'pending':
          return '#fbbf24'; // Yellow
        case 'skipped':
          return '#9ca3af'; // Gray
      }
    }

    // Node type colors
    switch (node.type) {
      case 'start':
        return '#10b981'; // Green
      case 'end':
        return '#ef4444'; // Red
      case 'agent':
        return '#8b5cf6'; // Purple
      case 'condition':
      case 'switch':
        return '#f59e0b'; // Orange
      case 'loop':
      case 'parallel':
        return '#06b6d4'; // Cyan
      case 'trigger':
      case 'webhook_trigger':
      case 'schedule_trigger':
        return '#ec4899'; // Pink
      case 'http_request':
        return '#3b82f6'; // Blue
      case 'slack':
      case 'discord':
      case 'email':
        return '#14b8a6'; // Teal
      case 'database':
        return '#6366f1'; // Indigo
      case 'code':
        return '#a855f7'; // Purple
      case 'comment':
        return '#fbbf24'; // Yellow
      case 'group':
        return '#94a3b8'; // Slate
      default:
        return '#6b7280'; // Gray
    }
  };

  // Node stroke color (border)
  const nodeStrokeColor = (node: Node) => {
    if (node.selected) {
      return '#3b82f6'; // Blue for selected
    }
    return nodeColor(node);
  };

  // Node class name for additional styling
  const nodeClassName = (node: Node) => {
    const classes = ['minimap-node'];
    
    if (node.selected) {
      classes.push('minimap-node-selected');
    }
    
    if (node.data?.executionStatus === 'running') {
      classes.push('minimap-node-running');
    }
    
    return classes.join(' ');
  };

  return (
    <>
      <MiniMap
        nodeColor={nodeColor}
        nodeStrokeColor={nodeStrokeColor}
        nodeClassName={nodeClassName}
        nodeBorderRadius={4}
        nodeStrokeWidth={2}
        maskColor="rgba(0, 0, 0, 0.1)"
        className={className}
        style={{
          backgroundColor: '#f9fafb',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        }}
        pannable
        zoomable
      />
      
      {/* Custom styles */}
      <style jsx global>{`
        .minimap-node {
          transition: all 0.2s ease;
        }
        
        .minimap-node-selected {
          filter: brightness(1.2);
          stroke-width: 3px !important;
        }
        
        .minimap-node-running {
          animation: minimap-pulse 2s infinite;
        }
        
        @keyframes minimap-pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.6;
          }
        }
        
        /* Dark mode support */
        .dark .react-flow__minimap {
          background-color: #1f2937 !important;
          border-color: #374151 !important;
        }
        
        .dark .react-flow__minimap-mask {
          fill: rgba(255, 255, 255, 0.1) !important;
        }
      `}</style>
    </>
  );
}
