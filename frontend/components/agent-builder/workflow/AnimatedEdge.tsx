'use client';

import { memo } from 'react';
import { EdgeProps, getBezierPath } from 'reactflow';
import { cn } from '@/lib/utils';

interface AnimatedEdgeData {
  status?: 'active' | 'inactive' | 'completed' | 'failed';
  animated?: boolean;
}

const AnimatedEdge = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  data,
  markerEnd,
}: EdgeProps<AnimatedEdgeData>) => {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const status = data?.status || 'inactive';
  const animated = data?.animated !== false;

  const getEdgeStyles = () => {
    switch (status) {
      case 'active':
        return {
          stroke: '#3b82f6', // blue-500
          strokeWidth: 2.5,
          className: animated ? 'animate-dash' : '',
        };
      case 'completed':
        return {
          stroke: '#22c55e', // green-500
          strokeWidth: 2,
          className: '',
        };
      case 'failed':
        return {
          stroke: '#ef4444', // red-500
          strokeWidth: 2,
          className: '',
        };
      default:
        return {
          stroke: '#94a3b8', // gray-400
          strokeWidth: 1.5,
          className: '',
        };
    }
  };

  const edgeStyles = getEdgeStyles();

  return (
    <>
      {/* Background glow for active edges */}
      {status === 'active' && (
        <path
          d={edgePath}
          fill="none"
          stroke="#3b82f6"
          strokeWidth={6}
          opacity={0.2}
          className="animate-pulse"
        />
      )}
      
      {/* Main edge path */}
      <path
        id={id}
        d={edgePath}
        fill="none"
        stroke={edgeStyles.stroke}
        strokeWidth={edgeStyles.strokeWidth}
        className={cn(
          'transition-all duration-300',
          edgeStyles.className
        )}
        strokeDasharray={status === 'active' && animated ? '5,5' : 'none'}
        markerEnd={markerEnd}
        style={style}
      />
      
      {/* Animated particles for active edges */}
      {status === 'active' && animated && (
        <>
          <circle r="3" fill="#3b82f6" className="animate-flow-particle-1">
            <animateMotion dur="2s" repeatCount="indefinite" path={edgePath} />
          </circle>
          <circle r="3" fill="#3b82f6" className="animate-flow-particle-2">
            <animateMotion dur="2s" repeatCount="indefinite" path={edgePath} begin="0.5s" />
          </circle>
        </>
      )}
    </>
  );
};

export default memo(AnimatedEdge);
