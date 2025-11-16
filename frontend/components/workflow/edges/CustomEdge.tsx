'use client';

import React from 'react';
import { EdgeProps, getBezierPath, EdgeLabelRenderer, BaseEdge } from 'reactflow';

// Get edge color based on handle type and execution state
const getEdgeColor = (
  sourceHandle?: string, 
  isInvalid?: boolean, 
  selected?: boolean,
  isExecuting?: boolean,
  executionStatus?: string
) => {
  if (isExecuting) return 'rgb(59 130 246)'; // blue for executing
  if (executionStatus === 'success') return 'rgb(16 185 129)'; // green for success
  if (executionStatus === 'error') return 'rgb(239 68 68)'; // red for error
  if (isInvalid) return 'rgb(239 68 68)'; // red for invalid
  if (selected) return 'rgb(59 130 246)'; // blue for selected
  
  // Condition node handle colors
  if (sourceHandle === 'true') return 'rgb(16 185 129)'; // green
  if (sourceHandle === 'false') return 'rgb(239 68 68)'; // red
  if (sourceHandle === 'default') return 'rgb(245 158 11)'; // amber
  
  return 'rgb(148 163 184)'; // default gray
};

export function CustomEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  data,
  selected,
  sourceHandleId,
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const edgeColor = getEdgeColor(
    sourceHandleId, 
    data?.isInvalid, 
    selected,
    data?.isExecuting,
    data?.executionStatus
  );
  
  // Determine if edge should be animated
  const isAnimated = data?.isExecuting || data?.executionStatus === 'success';
  const isError = data?.executionStatus === 'error';

  return (
    <>
      {/* Main edge path */}
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          strokeWidth: selected || data?.isExecuting ? 3 : 2,
          stroke: edgeColor,
          strokeDasharray: data?.isInvalid ? '5,5' : undefined,
        }}
      />
      
      {/* Animated overlay for data flow */}
      {isAnimated && !isError && (
        <path
          d={edgePath}
          fill="none"
          stroke={edgeColor}
          strokeWidth={selected || data?.isExecuting ? 3 : 2}
          strokeDasharray="5 5"
          className="edge-animated"
          style={{
            opacity: 0.6,
          }}
        />
      )}
      
      {/* Pulsing effect for executing edges */}
      {data?.isExecuting && (
        <path
          d={edgePath}
          fill="none"
          stroke={edgeColor}
          strokeWidth={6}
          className="animate-pulse"
          style={{
            opacity: 0.3,
          }}
        />
      )}
      
      {/* Error shake effect */}
      {isError && (
        <path
          d={edgePath}
          fill="none"
          stroke={edgeColor}
          strokeWidth={3}
          style={{
            animation: 'shake 0.5s',
            opacity: 0.8,
          }}
        />
      )}
      {data?.label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
            }}
            className="nodrag nopan bg-background border border-border rounded px-2 py-1 text-xs font-medium"
          >
            {data.label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}
