'use client';

/**
 * Execution MiniMap Component
 * 
 * Enhanced minimap with:
 * - Execution status colors
 * - Click to navigate
 * - Zoom controls
 * - Current viewport indicator
 */

import React, { useMemo, useCallback } from 'react';
import { MiniMap, useReactFlow, Node } from 'reactflow';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { ZoomIn, ZoomOut, Maximize, Target } from 'lucide-react';

interface NodeExecutionStatus {
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped' | 'waiting';
}

interface ExecutionMiniMapProps {
  nodeStatuses?: Record<string, NodeExecutionStatus>;
  className?: string;
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
  showControls?: boolean;
}

// Status to color mapping
const statusColors: Record<string, string> = {
  pending: '#9ca3af',    // gray-400
  running: '#3b82f6',    // blue-500
  success: '#22c55e',    // green-500
  failed: '#ef4444',     // red-500
  skipped: '#d1d5db',    // gray-300
  waiting: '#f59e0b',    // amber-500
  default: '#6366f1',    // indigo-500
};

export function ExecutionMiniMap({
  nodeStatuses = {},
  className,
  position = 'bottom-right',
  showControls = true,
}: ExecutionMiniMapProps) {
  const { fitView, zoomIn, zoomOut, setCenter, getNodes } = useReactFlow();

  // Get node color based on execution status
  const nodeColor = useCallback((node: Node) => {
    const status = nodeStatuses[node.id];
    if (status) {
      return statusColors[status.status] || statusColors.default;
    }
    
    // Default colors based on node type
    switch (node.type) {
      case 'start':
        return '#22c55e'; // green
      case 'end':
        return '#ef4444'; // red
      case 'condition':
        return '#f59e0b'; // amber
      case 'trigger':
        return '#8b5cf6'; // violet
      case 'loop':
      case 'parallel':
        return '#06b6d4'; // cyan
      default:
        return statusColors.default;
    }
  }, [nodeStatuses]);

  // Handle click on minimap to navigate
  const handleMiniMapClick = useCallback((event: React.MouseEvent, position: { x: number; y: number }) => {
    setCenter(position.x, position.y, { zoom: 1, duration: 500 });
  }, [setCenter]);

  // Focus on running nodes
  const focusOnRunning = useCallback(() => {
    const nodes = getNodes();
    const runningNodes = nodes.filter(node => nodeStatuses[node.id]?.status === 'running');
    
    if (runningNodes.length > 0) {
      fitView({ nodes: runningNodes, duration: 500, padding: 0.5 });
    }
  }, [getNodes, nodeStatuses, fitView]);

  // Check if any nodes are running
  const hasRunningNodes = useMemo(() => {
    return Object.values(nodeStatuses).some(s => s.status === 'running');
  }, [nodeStatuses]);

  // Position classes
  const positionClasses = {
    'top-left': 'top-4 left-4',
    'top-right': 'top-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-right': 'bottom-4 right-4',
  };

  return (
    <TooltipProvider>
      <div className={cn('absolute z-10', positionClasses[position], className)}>
        {/* Controls */}
        {showControls && (
          <div className="flex gap-1 mb-2 justify-end">
            {hasRunningNodes && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    size="sm"
                    variant="secondary"
                    className="h-7 w-7 p-0 animate-pulse"
                    onClick={focusOnRunning}
                  >
                    <Target className="h-3.5 w-3.5 text-blue-500" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Focus on running nodes</TooltipContent>
              </Tooltip>
            )}
            
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  size="sm"
                  variant="secondary"
                  className="h-7 w-7 p-0"
                  onClick={() => zoomIn({ duration: 200 })}
                >
                  <ZoomIn className="h-3.5 w-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Zoom in</TooltipContent>
            </Tooltip>
            
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  size="sm"
                  variant="secondary"
                  className="h-7 w-7 p-0"
                  onClick={() => zoomOut({ duration: 200 })}
                >
                  <ZoomOut className="h-3.5 w-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Zoom out</TooltipContent>
            </Tooltip>
            
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  size="sm"
                  variant="secondary"
                  className="h-7 w-7 p-0"
                  onClick={() => fitView({ duration: 500, padding: 0.2 })}
                >
                  <Maximize className="h-3.5 w-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Fit to view</TooltipContent>
            </Tooltip>
          </div>
        )}

        {/* MiniMap */}
        <div className="relative rounded-lg overflow-hidden border shadow-lg bg-background">
          <MiniMap
            nodeColor={nodeColor}
            nodeStrokeWidth={3}
            nodeBorderRadius={4}
            maskColor="rgba(0, 0, 0, 0.1)"
            className="!bg-muted/50"
            style={{
              width: 180,
              height: 120,
            }}
            pannable
            zoomable
          />
          
          {/* Status Legend */}
          <div className="absolute bottom-1 left-1 flex gap-1">
            {Object.values(nodeStatuses).some(s => s.status === 'running') && (
              <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-background/80 text-[10px]">
                <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                <span>Running</span>
              </div>
            )}
            {Object.values(nodeStatuses).some(s => s.status === 'failed') && (
              <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-background/80 text-[10px]">
                <div className="w-2 h-2 rounded-full bg-red-500" />
                <span>Failed</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}

// Standalone zoom controls component
interface ZoomControlsProps {
  className?: string;
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
}

export function ZoomControls({ className, position = 'bottom-left' }: ZoomControlsProps) {
  const { fitView, zoomIn, zoomOut, zoomTo } = useReactFlow();

  const positionClasses = {
    'top-left': 'top-4 left-4',
    'top-right': 'top-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-right': 'bottom-4 right-4',
  };

  return (
    <TooltipProvider>
      <div className={cn(
        'absolute z-10 flex flex-col gap-1 p-1 rounded-lg bg-background border shadow-md',
        positionClasses[position],
        className
      )}>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0"
              onClick={() => zoomIn({ duration: 200 })}
            >
              <ZoomIn className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Zoom in (Ctrl++)</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0"
              onClick={() => zoomOut({ duration: 200 })}
            >
              <ZoomOut className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Zoom out (Ctrl+-)</TooltipContent>
        </Tooltip>

        <div className="h-px bg-border my-1" />

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0"
              onClick={() => zoomTo(1, { duration: 200 })}
            >
              <span className="text-xs font-mono">1:1</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent>Reset zoom to 100%</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0"
              onClick={() => fitView({ duration: 500, padding: 0.2 })}
            >
              <Maximize className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Fit to view</TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
}
